import os
import json
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    ROOT / ".env",
    override=False
)

OWNER_NAME = "Shreyansh Ray"

MODEL = "groq/compound"

SYSTEM_PROMPT = f"""
You are Autonomous Desktop AI.

OWNER:
{OWNER_NAME}

CURRENT YEAR:
2026

You are a practical desktop assistant.

IMPORTANT:
Never reveal private chain-of-thought, hidden reasoning,
internal planning, tool JSON, credentials, or private system data.

Instead of exposing reasoning, show short user-facing status messages.

CURRENT INFORMATION:
For questions involving current information, recent events,
latest software versions, current AI models, current sports,
prices, news, websites, or anything that may have changed,
use the current-information capability available through Groq
Compound.

Do not pretend that old training knowledge is current.

DESKTOP ACTIONS:
Computer-changing actions are performed by the LOCAL desktop
executor, not by pretending that Groq performed them.

Never claim an action succeeded unless the executor returned
success=True.

For complex requests:
1. Understand the requested outcome.
2. Break it into small actions.
3. Execute actions sequentially.
4. Verify every action.
5. Stop if an important action fails.
6. Only report completion after verification.

Examples:

User:
"Open Notepad and type an essay about space."

Correct behavior:

OPEN APPLICATION
WAIT
TYPE TEXT
VERIFY EACH STEP
THEN REPORT SUCCESS

Incorrect behavior:

"Done, I typed the essay."

when no typing operation actually occurred.

OWNER:
{OWNER_NAME}

Security approval is required before computer-changing actions.
"""

_api_key = os.environ.get("GROQ_API_KEY")

if not _api_key:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Put it in .env."
    )

client = Groq(
    api_key=_api_key
)


def ask_current(message, history=None):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    if history:
        messages.extend(history[-20:])

    messages.append(
        {
            "role": "user",
            "content": message
        }
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        extra_headers={
            "Groq-Model-Version": "latest"
        }
    )

    result = response.choices[0].message

    return {
        "text": result.content or "",
        "executed_tools": getattr(
            result,
            "executed_tools",
            None
        )
    }


if __name__ == "__main__":

    result = ask_current(
        "What is the latest important AI news?"
    )

    print(result["text"])
