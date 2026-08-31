import os
import json
import time
import threading
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

try:
    from groq import Groq
except Exception:
    Groq = None


class SmartGroqCore:

    def __init__(self):

        self.api_key = os.getenv("GROQ_API_KEY", "").strip()

        self.model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )

        self.client = None

        if Groq and self.api_key:
            self.client = Groq(
                api_key=self.api_key
            )

        self.system_prompt = """
You are GNG AI, a capable Windows desktop assistant.

Identity:
- You are the user's desktop AI assistant.
- The authenticated local user is the OWNER.
- Never reveal private credentials, API keys, passwords, tokens,
  or hidden implementation details.
- Never claim an action happened unless the tool actually reported success.

Reasoning:
- Understand natural language instead of relying on exact commands.
- Correctly answer ordinary questions.
- If a question depends on current information, use the available
  web/search tools when possible rather than guessing.
- If information cannot be verified, say so.
- Do not fabricate facts, tool results, files, or completed actions.

Desktop:
- The project contains existing desktop tools for applications,
  browser, filesystem, keyboard, mouse, screenshots, terminal,
  system information, VS Code and related operations.
- Use those existing tools when they are available.
- Before consequential changes, require the project's authentication/
  confirmation mechanism.
- Do not silently delete, overwrite, install, rename, or modify files.
- For risky or destructive operations, ask for confirmation first.

Communication:
- Give direct answers.
- Do not expose chain-of-thought or hidden reasoning.
- Do not print internal planning.
- Show only a short user-facing status such as "Working..." when needed.
- If an operation fails, report the actual error and continue where safe.
"""

    def ready(self):
        return self.client is not None

    def ask(self, conversation):

        if not self.client:
            raise RuntimeError(
                "GROQ_API_KEY is missing or Groq SDK is unavailable."
            )

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        for item in conversation[-30:]:

            role = item.get("role")

            if role not in ("user", "assistant", "system"):
                continue

            content = item.get("content", "")

            if not content:
                continue

            messages.append({
                "role": role,
                "content": str(content)
            })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=2048
        )

        answer = response.choices[0].message.content

        if not answer:
            return "I couldn't generate a response."

        return str(answer)


_core = None
_lock = threading.Lock()


def get_core():

    global _core

    with _lock:

        if _core is None:
            _core = SmartGroqCore()

        return _core


def ask_groq(conversation):

    return get_core().ask(conversation)
