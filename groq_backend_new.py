import os
from dotenv import load_dotenv

load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env"
    )
)

try:
    from groq import Groq
except Exception:
    Groq = None

MODEL = "groq/compound"

SYSTEM_PROMPT = """
You are the user's Windows desktop AI assistant.

Rules:
- Give concise, useful answers.
- Never expose private chain-of-thought or hidden reasoning.
- If the user asks for current/recent information, use Groq's current-information capability when available.
- Never claim that you changed the computer unless a local tool actually performed the action.
- Distinguish clearly between planning an action and successfully executing it.
- For destructive or consequential computer actions, require explicit confirmation from the user.
- Do not invent facts, tool results, file contents, or successful computer actions.
"""

class GroqBrain:

    def __init__(self):
        key = os.getenv("GROQ_API_KEY")

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Put it in the project's .env file."
            )

        if Groq is None:
            raise RuntimeError(
                "Groq SDK is not installed."
            )

        self.client = Groq(api_key=key)

    def ask(self, history, user_message):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for item in history[-20:]:
            if item.get("role") in ("user", "assistant"):
                messages.append({
                    "role": item["role"],
                    "content": str(item["content"])
                })

        messages.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        text = response.choices[0].message.content

        if not text:
            return "I received an empty response."

        return str(text)