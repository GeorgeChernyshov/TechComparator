import os
from openai import OpenAI

def run_simple_assistant():
    client = OpenAI()
    user_prompt = input("Input: ")

    messages = [
        {
            "role": "user", 
            "content": user_prompt
        }
    ]

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages
    )

    ai_response = response.choices[0].message.content
    print(f"\nAssistant: {ai_response}")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: Environment variable OPENAI_API_KEY is not defined!")
    else:
        run_simple_assistant()