import os
import json
from datetime import datetime


class Memory:

    def __init__(self):

        root = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        self.path = os.path.join(
            root,
            "logs",
            "conversation_memory.json"
        )

        os.makedirs(
            os.path.dirname(self.path),
            exist_ok=True
        )

        self.messages = []
        self.load()

    def load(self):

        try:

            if os.path.exists(self.path):

                with open(
                    self.path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                if isinstance(data, list):
                    self.messages = data

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
                    self.messages[-80:],
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception:
            pass

    def add(self, role, content):

        self.messages.append({
            "role": role,
            "content": str(content),
            "time": datetime.now().isoformat()
        })

        self.save()

    def recent(self, limit=12):

        return self.messages[-limit:]

    def clear(self):

        self.messages = []
        self.save()

