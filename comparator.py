import os
from openai import OpenAI
import sqlite3
import json
import requests
from bs4 import BeautifulSoup
import urllib.parse

DB_FILE = "tech_knowledge.db"

client = OpenAI()
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."}
]

tools = [
    {
        "type": "function",
        "function": {
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

def web_search(query: str, max_results: int = 4) -> str:
    print(f"[Tool] Running web search for: '{query}'")
    
    url = f"https://duckduckgo.com{urllib.parse.quote(query)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Error: response code {response.status_code}"
            
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        links = soup.find_all("div", class_="result__body")
        
        for link in links[:max_results]:
            title_element = link.find("a", class_="result__url")
            snippet_element = link.find("a", class_="result__snippet")
            
            if title_element and snippet_element:
                title = title_element.text.strip()
                raw_href = title_element["href"]
                parsed_url = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                clean_url = parsed_url.get("uddg", [raw_href])[0]
                
                snippet = snippet_element.text.strip()
                
                results.append(f"Title: {title}\nUrl: {clean_url}\nDescription: {snippet}\n---")
                
        if not results:
            return "No results. Try changing the request wording."
            
        return "\n\n".join(results)
        
    except Exception as e:
        return f"Error while running web search: {str(e)}"

def run_assistant(user_input):
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages,
        tools=tools,
        parallel_tool_calls=False
    )

    ai_response = response.choices[0].message.content
    messages.append({"role": "assistant", "content": ai_response})
    print(f"\nAssistant: {ai_response}")

def main_loop():
    print("--- Assiatant started. Write 'exit' to quit. ---\n")

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
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: Environment variable OPENAI_API_KEY is not defined!")
    else:
        init_agent_database()
        main_loop()