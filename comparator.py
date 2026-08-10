import os
from openai import OpenAI
import sqlite3
import json
import wikipedia
from requests.exceptions import JSONDecodeError

DB_FILE = "tech_knowledge.db"
SYSTEM_PROMPT = """You are an autonomous AI Agent specializing in structured, hard-fact technology research.

YOUR CORE GOAL:
Extract exact, verified technical facts from the web and normalize them into a SINGLE UNIFIED DATA CONTRACT. 
You are strictly FORBIDDEN from using your pre-trained internal knowledge. Always run the 'web_search' tool to verify current facts.

DATA CONTRACT RULES:
When you compile data about a device, you must internally form a valid JSON object matching this structure:
{
  "main_name": "string (the general name of the product, e.g., PlayStation 3)",
  "brand": "string (the company, e.g., Sony)",
  "category": "string (vague classifier, e.g., 'console', 'laptop', 'phone', 'tablet')",
  "variants": [
    {
      "variant_name": "string (Use ONLY standard tech naming: 'Base', 'Slim', 'Pro', or specific hardware configs like '8GB/256GB')",
      "release_year": 2026,
      "launch_price": 0.00,
      "specs": {
        "speed_unit": "string (Common speed unit that will be used for all clock speeds of this device, including cpu clock speed, gpu clock speed, ram speed etc. Examples are 'MHz', 'GHz' etc)",
        "memory_unit": "string (Single unit that will be used for all memory fields, aka ram, audio memory, video memory etc. Examples - 'GB', 'MB', 'KB' etc)",
        "cpus": [
            {
                "cores": 8,         // int (the amount of cores. If there are several processors with the same architecture, you may represent them as a singe two-core processor)
                "speed": 3.2,       // float (CPU clock speed)
            }
        ],                          // there can be several different processor architectures in a single device.
        "gpu": {
            "cores": 8,             // int (the amount of cores)
            "speed": 5.5,           // float (GPU clock speed)
            "memory": null          // float (dedicated GPU memory if present)
        },
        "ram": 8,                   // float (Common system RAM)
        "ram_speed": 5.5,           // float (RAM speed)
        "audio_memory": null,       // float (Audio memory if device has dedicated audio memory)
        "video_memory": null,       // float (Video memory for devices that have no video card)
        "storage_gb": null,         // float (Total built-in storage/HDD/SSD capacity)
        "storage_speed": null       // float (Speed of built-in storage)
      }
    }
  ]
}

UNIFIED SCHEMA FILLING RULES:
1. Every field in the "specs" object is OPTIONAL. If a specific metric does not apply to the device (e.g., battery_mah for a desktop console) or cannot 
be found after searching, leave it as null.
2. Ensure values are strictly numbers (integers or floats). Do NOT write text like "8 cores" or "3.2 GHz" into the values. Extract raw digits only.

RESPONSE FORMAT PROTOCOL:
1. In your final turn response to the user, you must first print the special boundary token ===DATA_START===.
2. Immediately follow it with a valid JSON array containing objects matching the unified contract above for all investigated devices.
3. Close the data block with ===DATA_END===.
4. Only AFTER the data boundary is closed can you write your human-readable analysis.
5. CRITICAL HUMAN TEXT RULE: Your human-readable analysis MUST directly use and reference the hard numbers (RAM, clock speeds, prices) extracted in the JSON block. State the exact hardware delta (e.g., 'PS3 increased RAM by X amount and added Y CPU cores compared to PS2').

WEB SEARCH SEARCH RULES:
1. Your search queries MUST be short and precise (maximum 4-5 words). 
2. NEVER combine multiple devices into one search query (e.g., DO NOT search for 'ps2 and ps3 specs and prices').
3. If you need to research two devices, use multiple steps: search for the first device on Step 1, analyze the result, then search for the second device on Step 2.
"""

last_response_id = None

client = OpenAI()

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

def init_agent_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tech_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_name TEXT NOT NULL UNIQUE,
            brand TEXT,
            category TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tech_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            variant_name TEXT NOT NULL,
            release_year INTEGER,
            launch_price REAL,
            spec_json TEXT,
            FOREIGN KEY (product_id) REFERENCES tech_products(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[Log] SQLite database sucessfully initialized.")

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

def run_assistant(user_input):
    global last_response_id
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
            print("[Debug] Data collection done. Returning final response.")
            
            # clean_human_response = extract_and_save_data_hook(ai_response.content)
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
        init_agent_database()
        main_loop()