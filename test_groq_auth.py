import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"

print("=" * 60)
print(" GNG AI GROQ AUTH TEST")
print("=" * 60)

print("Project:", ROOT)
print(".env exists:", ENV_FILE.exists())

if not ENV_FILE.exists():
    raise SystemExit(".env file does not exist.")

key = None

for raw_line in ENV_FILE.read_text(
    encoding="utf-8-sig"
).splitlines():

    line = raw_line.strip()

    if not line:
        continue

    if line.startswith("#"):
        continue

    if line.startswith("GROQ_API_KEY="):
        key = line.split("=", 1)[1].strip()
        break

if not key:
    raise SystemExit(
        "GROQ_API_KEY was not found inside .env"
    )

os.environ["GROQ_API_KEY"] = key

print("GROQ_API_KEY: FOUND")
print("KEY LENGTH:", len(key))
print("KEY PRINTED:", "NO")

try:
    from groq import Groq
except Exception as e:
    raise SystemExit(
        "Groq SDK import failed: " + str(e)
    )

client = Groq(api_key=key)

print("")
print("Testing Groq API...")
print("")

try:

    response = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are GNG AI. "
                    "Give only the final answer. "
                    "Never reveal private reasoning or "
                    "internal tool information."
                )
            },
            {
                "role": "user",
                "content": "Reply with exactly: GNG AI ONLINE"
            }
        ]
    )

    answer = response.choices[0].message.content

    print("=" * 60)
    print(" GROQ CONNECTION SUCCESS")
    print("=" * 60)
    print("")
    print(answer)
    print("")

except Exception as e:

    print("=" * 60)
    print(" GROQ REQUEST FAILED")
    print("=" * 60)
    print("")
    print(type(e).__name__)
    print(str(e))
    print("")

    raise