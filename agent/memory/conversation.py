import json
import os
from datetime import datetime


class ConversationMemory:

    def __init__(self):

        self.path = os.path.abspath(
            "logs/conversation_memory.json"
        )

        os.makedirs(
            os.path.dirname(self.path),
            exist_ok=True
        )

        self.messages = []

        self.load()

    def load(self):

        if not os.path.exists(self.path):
            return

        try:

            with open(
                self.path,
                "r",
                encoding="utf-8"
            ) as f:

                self.messages = json.load(f)

        except Exception:

            self.messages = []

    def save(self):

        try:

            with open(
                self.path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.messages,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception:
            pass

    def add(self, role, content):

        self.messages.append(
            {
                "role": role,
                "content": content,
                "time": datetime.now().isoformat()
            }
        )

        # Keep memory small and fast
        if len(self.messages) > 100:

            self.messages = self.messages[-100:]

        self.save()

    def recent(self, limit=8):

        return self.messages[-limit:]

    def context(self, limit=8):

        recent = self.recent(limit)

        parts = []

        for item in recent:

            parts.append(
                item["role"].upper()
                + ": "
                + item["content"]
            )

        return "\n".join(parts)

    def clear(self):

        self.messages = []

        self.save()
