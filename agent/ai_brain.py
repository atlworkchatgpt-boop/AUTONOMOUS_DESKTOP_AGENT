import json
import urllib.error
import urllib.request

from config.config import (
    AI_CONTEXT_MESSAGES,
    AI_MAX_OUTPUT,
    AI_MODEL,
    AI_TIMEOUT,
    OLLAMA_URL,
    OWNER_NAME,
)


SYSTEM_PROMPT = f"""
You are Autonomous Desktop AI.

Creator and owner:
{OWNER_NAME}

You are a local Windows computer assistant.

You have two jobs:

1. Answer questions.
2. Produce structured plans for explicitly requested computer actions.

NEVER perform actions on your own.

For normal questions return JSON:

{{
    "action": "chat",
    "args": {{}},
    "message": "answer"
}}

For a computer action return JSON:

{{
    "action": "action_name",
    "args": {{}},
    "message": "short explanation"
}}

Allowed actions:

open_app
open_url

browser_search
browser_open_url
browser_back
browser_forward
browser_refresh
browser_type
browser_click
browser_read_page

open_folder
list_files
read_file
create_file

screenshot

type_text
press_key
press_hotkey
move_mouse
click_mouse

read_clipboard
write_clipboard

system_info
processes
terminal

delete
install
close

IMPORTANT:

Only create an action when the owner explicitly asks.

Never claim that an action succeeded.
The Python application will execute it and report the result.

Deleting, installing, and closing are protected by TWO confirmation dialogs.

Computer-changing actions require owner authentication.

Starting applications requires startup authentication.

Keep responses short.
"""


class AIBrain:

    def __init__(self):

        self.history = []

    def _request(self, messages):

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "stream": False,
            "keep_alive": "1m",
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": 768,
                "num_predict": AI_MAX_OUTPUT,
            },
        }

        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=AI_TIMEOUT,
            ) as response:

                return json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.URLError as exc:

            raise RuntimeError(
                "Ollama is not responding."
            ) from exc

    def ask(self, text):

        self.history = self.history[
            -AI_CONTEXT_MESSAGES:
        ]

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        messages.extend(
            self.history
        )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        result = self._request(
            messages
        )

        content = (
            result
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:

            return {
                "action": "chat",
                "args": {},
                "message": (
                    "I didn't receive a response."
                ),
            }

        try:

            parsed = json.loads(
                content
            )

        except json.JSONDecodeError:

            parsed = {
                "action": "chat",
                "args": {},
                "message": content,
            }

        if not isinstance(
            parsed,
            dict
        ):

            parsed = {
                "action": "chat",
                "args": {},
                "message": str(parsed),
            }

        action = parsed.get(
            "action",
            "chat"
        )

        args = parsed.get(
            "args",
            {}
        )

        message = parsed.get(
            "message",
            ""
        )

        if not isinstance(
            args,
            dict
        ):
            args = {}

        self.history.append(
            {
                "role": "user",
                "content": text,
            }
        )

        self.history.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    parsed
                ),
            }
        )

        return {
            "action": action,
            "args": args,
            "message": str(message),
        }
