import json
import os
from agent.config import MEMORY_FILE, MAX_HISTORY


class Memory:

    def __init__(self):
        self.messages = []
        self.load()

    def load(self):

        if not os.path.exists(MEMORY_FILE):
            return

        try:
            with open(
                MEMORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                self.messages = json.load(f)

        except Exception:
            self.messages = []

    def save(self):

        try:
            with open(
                MEMORY_FILE,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    self.messages[-MAX_HISTORY * 2:],
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception:
            pass

    def add(self, role, content):

        self.messages.append({
            "role": role,
            "content": content
        })

        self.messages = self.messages[
            -(MAX_HISTORY * 2):
        ]

        self.save()

    def recent(self):

        return self.messages[-MAX_HISTORY * 2:]

    def clear(self):

        self.messages = []
        self.save()
