import os
import sqlite3
import json
import wikipedia
from dataclasses import asdict
from requests.exceptions import JSONDecodeError
from pathlib import Path
from openai import OpenAI
from src.database import (
    find_product as find_product_in_database,
    find_product_id,
    init_agent_database,
    save_research_results,
)

from src.product import Product, ProductVariant
from src.comparison import compare_products as calculate_comparison

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
        "name": "find_product",
        "description": (
            "Looks up one product in the local database by its general name. "
            "Use this before web_search. If it returns a product, use its "
            "stored variants and specifications; if it reports no match, "
            "research that product on the web."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "One product name, such as 'PlayStation 3'.",
                }
            },
            "required": ["product_name"],
            "additionalProperties": False,
        },
    },
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
    },
    {
        "type": "function",
        "name": "save_product",
        "description": (
            "Validate and save one newly researched product to the local "
            "database. Call this after researching a product that was not "
            "found by find_product."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "object",
                    "properties": {
                        "main_name": {"type": "string"},
                        "brand": {"type": "string"},
                        "category": {"type": "string"},
                        "variants": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "variant_name": {"type": "string"},
                                    "release_year": {"type": "integer"},
                                    "launch_price": {"type": "number"},
                                    "specs": {
                                        "type": "object",
                                        "properties": {
                                            "speed_unit": {"type": ["string", "null"]},
                                            "memory_unit": {"type": ["string", "null"]},
                                            "cpus": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "cores": {"type": ["integer", "null"]},
                                                        "speed": {"type": ["number", "null"]},
                                                        "ops_per_cycle": {"type": ["number", "null"]},
                                                    },
                                                },
                                            },
                                            "gpu": {
                                                "type": ["object", "null"],
                                                "properties": {
                                                    "cores": {"type": ["integer", "null"]},
                                                    "speed": {"type": ["number", "null"]},
                                                    "ops_per_cycle": {"type": ["number", "null"]},
                                                    "memory_bandwidth": {"type": ["number", "null"]},
                                                    "memory": {"type": ["number", "null"]},
                                                },
                                            },
                                            "ram": {"type": ["number", "null"]},
                                            "ram_bandwidth": {"type": ["number", "null"]},
                                            "audio_memory": {"type": ["number", "null"]},
                                            "video_memory": {"type": ["number", "null"]},
                                            "storage_gb": {"type": ["number", "null"]},
                                            "storage_speed": {"type": ["number", "null"]},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "required": ["product"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "compare_products",
        "description": (
            "Calculate the raw directional comparison score A/B for two "
            "selected variants. The score is the product "
            "of all numeric technical-specification ratios. Missing or zero "
            "values contribute 1. Do not normalize this result."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "variant_a": {
                    "type": "object",
                    "description": "The selected numerator variant from product A.",
                },
                "variant_b": {
                    "type": "object",
                    "description": "The selected denominator variant from product B.",
                },
            },
            "required": ["variant_a", "variant_b"],
            "additionalProperties": False,
        },
    },
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

def find_product(product_name: str) -> str:
    """Expose a database lookup result to the model as JSON."""
    product = find_product_in_database(product_name, DB_FILE)
    product_id = find_product_id(product_name, DB_FILE) if product else None
    return json.dumps(
        {
            "found": product is not None,
            "product_id": product_id,
            "product": asdict(product) if product else None,
        },
        ensure_ascii=False,
    )


def save_product(product_data: dict) -> str:
    """Validate and persist one product supplied by the model."""
    product = Product.from_dict(product_data)
    counts = save_research_results([product], DB_FILE)
    product_id = find_product_id(product.main_name, DB_FILE)

    if product_id is None:
        raise RuntimeError("Product was saved but could not be read back.")

    return json.dumps(
        {
            "saved": True,
            "product_id": product_id,
            "product_name": product.main_name,
            "counts": counts,
        },
        ensure_ascii=False,
    )


def compare_products(
    variant_a_data: dict,
    variant_b_data: dict,
) -> str:
    """Calculate and return one raw A/B comparison score."""
    score = calculate_comparison(
        ProductVariant.from_dict(variant_a_data),
        ProductVariant.from_dict(variant_b_data),
    )
    return json.dumps({"score": score}, ensure_ascii=False)

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
    max_steps = 15
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
                
                try:
                    if tool_name == "find_product":
                        observation = find_product(
                            product_name=tool_args["product_name"],
                        )
                    elif tool_name == "web_search":
                        observation = web_search(query=tool_args["query"])
                    elif tool_name == "save_product":
                        observation = save_product(
                            product_data=tool_args["product"],
                        )
                    elif tool_name == "compare_products":
                        observation = compare_products(
                            variant_a_data=tool_args["variant_a"],
                            variant_b_data=tool_args["variant_b"],
                        )
                    else:
                        observation = f"Error: tool {tool_name} not found"
                except (ValueError, KeyError, TypeError, RuntimeError, sqlite3.Error) as error:
                    observation = f"Tool '{tool_name}' failed: {error}"

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
                parse_products_response(response.output_text)
            except ValueError as error:
                print(f"[Error] Final result failed validation: {error}")

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
