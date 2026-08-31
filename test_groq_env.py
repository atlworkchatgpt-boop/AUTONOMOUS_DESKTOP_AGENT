import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

key = os.getenv("GROQ_API_KEY")

if not key:
    print("GROQ_API_KEY NOT FOUND")
    raise SystemExit(1)

print("GROQ_API_KEY FOUND")
print("Length:", len(key))

# Make it available to everything launched by this process
os.environ["GROQ_API_KEY"] = key

from groq import Groq

client = Groq(api_key=key)

response = client.chat.completions.create(
    model="groq/compound",
    messages=[
        {
            "role": "system",
            "content": (
                "You are GNG AI. Give only the final answer. "
                "Do not expose private reasoning or internal tool details. "
                "Use current web information when appropriate."
            )
        },
        {
            "role": "user",
            "content": "What is the current date?"
        }
    ]
)

print("")
print("============================================================")
print("GROQ CONNECTION SUCCESSFUL")
print("============================================================")
print("")
print(response.choices[0].message.content)
