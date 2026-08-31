import os
from groq import Groq

print("")
print("=" * 60)
print(" GNG AI - LIVE AI TEST")
print("=" * 60)

key = os.environ.get("GROQ_API_KEY")

print("GROQ API KEY:", "FOUND" if key else "MISSING")

if not key:
    raise SystemExit(
        "GROQ_API_KEY is missing from this PowerShell session."
    )

client = Groq(
    api_key=key,
    default_headers={
        "Groq-Model-Version": "latest"
    }
)

print("MODEL: groq/compound")
print("LIVE WEB SEARCH: ENABLED")
print("INTERNAL REASONING DISPLAY: DISABLED")
print("")

response = client.chat.completions.create(
    model="groq/compound",
    messages=[
        {
            "role": "system",
            "content": (
                "Answer only with the final answer. "
                "Do not reveal reasoning or tool internals. "
                "For current facts, verify them using web search."
            )
        },
        {
            "role": "user",
            "content": (
                "What is the current FIFA World Cup situation? "
                "Use current web information and give a short answer."
            )
        }
    ]
)

print("ANSWER:")
print(response.choices[0].message.content)

print("")
print("=" * 60)
print("LIVE TEST PASSED")
print("=" * 60)