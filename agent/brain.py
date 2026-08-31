import json
import urllib.request

from config.config import (
    AI_MODEL,
)


OLLAMA_URL = (
    "http://127.0.0.1:11434/api/chat"
)


class SmartBrain:

    def __init__(self):

        self.history = []

    def _instant(
        self,
        text,
    ):

        value = text.strip().lower()

        replies = {
            "hi": "Hey! How can I help?",
            "hello": "Hey! How can I help?",
            "hey": "Hey! How can I help?",
            "thanks": "You're welcome!",
            "thank you": "You're welcome!",
            "who are you": (
                "I'm Autonomous Desktop AI, "
                "created and owned by Shreyansh Ray."
            ),
        }

        return replies.get(
            value
        )

    def ask(
        self,
        text,
        memory_context="",
    ):

        instant = self._instant(
            text
        )

        if instant:

            return True, instant

        system = (
            "You are Autonomous Desktop AI, "
            "created and owned by Shreyansh Ray.\n\n"
            "Be intelligent, accurate, and concise.\n"
            "Answer the user's actual request.\n"
            "Do not invent facts.\n"
            "Do not claim that you opened, changed, "
            "deleted, installed, clicked, or searched "
            "anything unless a tool actually did it.\n"
            "Computer actions are performed by Python tools.\n"
            "Current factual information should come from "
            "the web-search layer when available."
        )

        if memory_context:

            system += (
                "\n\nRelevant previous agent experience:\n"
                + memory_context
            )

        messages = [
            {
                "role": "system",
                "content": system,
            }
        ]

        messages.extend(
            self.history[-4:]
        )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.15,
                "num_ctx": 1024,
                "num_predict": 256,
                "num_thread": 2,
                "repeat_penalty": 1.05,
            },
        }

        request = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=180,
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            answer = (
                data
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not answer:

                return False, (
                    "The local AI returned no answer."
                )

            self.history.extend(
                [
                    {
                        "role": "user",
                        "content": text,
                    },
                    {
                        "role": "assistant",
                        "content": answer,
                    },
                ]
            )

            self.history = self.history[-4:]

            return True, answer

        except Exception as exc:

            return False, (
                "Local AI error: "
                + str(exc)
            )