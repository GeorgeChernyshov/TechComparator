import os
import sqlite3
import json
import wikipedia
from requests.exceptions import JSONDecodeError
from pathlib import Path
from openai import OpenAI
from src.database import init_agent_database, save_research_results
from src.product import Product

DB_FILE = "tech_knowledge.db"
DATA_START = "===DATA_START==="
DATA_END = "===DATA_END==="
SYSTEM_PROMPT = Path(__file__).resolve().with_name("SYSTEM_PROMPT.md").read_text(
    encoding="utf-8"
)

last_response_id = None
client: OpenAI | None = None

tools = [
    {
        "type": "function",
        "name": "web_search",
        "description": (
            "Runs web search through DuckDuckGo. "
            "Use this tool if you don't have precise data in the context window, "
            "you need to find actual prices of tech, find precise specifications, "
            "new model releases or compare gadgets that are not in the local database."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search request in english. "
                        "Make it precise, like: 'iPhone 2G launch price 2007' "
                        "or 'PlayStation 3 Slim features memory'."
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
]

def web_search(query: str, limit: int = 4) -> str:
    lines = []
    try:
        for index, title in enumerate(wikipedia.search(query, results=limit), start=1):
            page = wikipedia.page(title, auto_suggest=False)
            lines.append(f"{index}. {page.title}")
            lines.append(f"   {page.url}")
            lines.append(f"   {page.summary.splitlines()[0]}")
    except JSONDecodeError:
        return "Web search failed: Wikipedia returned a non-JSON response."

    return "\n".join(lines) if lines else "No results."


def parse_products_response(response_text: str) -> list[Product]:
    start = response_text.find(DATA_START)
    if start == -1:
        raise ValueError(f"Missing '{DATA_START}'.")

    start += len(DATA_START)
    end = response_text.find(DATA_END, start)
    if end == -1:
        raise ValueError(f"Missing '{DATA_END}'.")

    decoded = json.loads(response_text[start:end].strip())
    if not isinstance(decoded, list) or not decoded:
        raise ValueError("The data block must be a non-empty array.")
    if not all(isinstance(item, dict) for item in decoded):
        raise ValueError("Every product must be an object.")

    return [Product.from_dict(item) for item in decoded]

def run_assistant(user_input):
    global last_response_id
    if client is None:
        raise RuntimeError("OpenAI client has not been initialized.")

    pending_input = user_input
    previous_id = last_response_id
    max_steps = 6
    step = 0

    while step < max_steps:
        step += 1
        request = {
            "model": "gpt-5.6-terra",
            "instructions": SYSTEM_PROMPT,
            "input": pending_input,
            "tools": tools,
            "parallel_tool_calls": False,
            "reasoning": {"effort": "medium"},
        }

        if previous_id is not None:
            request["previous_response_id"] = previous_id

        response = client.responses.create(**request)

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if function_calls:
            tool_outputs = []

            for tool_call in function_calls:
                tool_name = tool_call.name
                tool_args = json.loads(tool_call.arguments)

                print(f"[Log] Calling tool '{tool_name}' with arguments: {tool_args}")
                
                if tool_name == "web_search":
                    observation = web_search(query=tool_args["query"])
                else:
                    observation = f"Error: tool {tool_name} not found"

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": observation,
                    }
                )

            previous_id = response.id
            pending_input = tool_outputs

        elif response.output_text:
            last_response_id = response.id

            try:
                products = parse_products_response(response.output_text)
                counts = save_research_results(products, DB_FILE)
                print(
                    "[Log] Database saved: "
                    f"{counts['products_inserted']} products inserted, "
                    f"{counts['products_updated']} products updated, "
                    f"{counts['variants_inserted']} variants inserted, "
                    f"{counts['variants_updated']} variants updated."
                )
            except (ValueError, sqlite3.Error) as error:
                print(f"[Error] Result was not saved: {error}")

            print("[Debug] Data collection done. Returning final response.")
            print(response.output_text)
            return response.output_text

    return "[Error] Agent went over the step limit and could not complete a task."

def main_loop():
    print("--- Assistant started. Write 'exit' to quit. ---\n")

    while True:
        user_input = input("Input: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        if not user_input:
            continue

        print("[Log] Processing your request...")

        try:
            run_assistant(user_input)

        except Exception as e:
            print(f"\n[Error]: {e}\n")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: Environment variable OPENAI_API_KEY is not defined!")
    else:
        client = OpenAI()
        init_agent_database(DB_FILE)
        main_loop()
