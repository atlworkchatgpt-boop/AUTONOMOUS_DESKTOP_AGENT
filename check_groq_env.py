import os
from pathlib import Path

print("")
print("=" * 60)
print(" GNG AI - ENVIRONMENT DIAGNOSTIC")
print("=" * 60)

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"

print("PROJECT:", ROOT)
print(".env exists:", ENV.exists())

if not ENV.exists():
    print("")
    print("ERROR: .env does not exist.")
    raise SystemExit(1)

# Read .env directly.
# This avoids depending on PowerShell environment variables.

key = None

for line in ENV.read_text(
    encoding="utf-8-sig"
).splitlines():

    line = line.strip()

    if not line:
        continue

    if line.startswith("#"):
        continue

    if line.startswith("GROQ_API_KEY="):

        key = line.split(
            "=",
            1
        )[1].strip()

        # Remove optional surrounding quotes.
        if (
            len(key) >= 2
            and key[0] == key[-1]
            and key[0] in ("'", '"')
        ):
            key = key[1:-1]

        break

if not key:

    print("")
    print("ERROR: GROQ_API_KEY was not found inside .env")
    print("")
    print("Your .env must contain:")
    print("GROQ_API_KEY=YOUR_NEW_KEY")
    raise SystemExit(1)

os.environ["GROQ_API_KEY"] = key

print("GROQ_API_KEY found in .env: YES")
print("KEY LENGTH:", len(key))
print("KEY PRINTED: NO")

try:

    from groq import Groq

    client = Groq(
        api_key=key
    )

    print("")
    print("Testing Groq API...")

    response = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are GNG AI. "
                    "Return only the final answer. "
                    "Never expose private reasoning."
                )
            },
            {
                "role": "user",
                "content": "Reply with exactly GNG AI ONLINE"
            }
        ]
    )

    answer = response.choices[0].message.content

    print("")
    print("=" * 60)
    print(" GROQ CONNECTION SUCCESS")
    print("=" * 60)
    print("")
    print(answer)
    print("")

except Exception as e:

    print("")
    print("=" * 60)
    print(" GROQ REQUEST FAILED")
    print("=" * 60)
    print("")
    print(type(e).__name__)
    print(str(e))
    print("")

    raise