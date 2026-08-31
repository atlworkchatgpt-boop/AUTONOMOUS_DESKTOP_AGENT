import json
from pathlib import Path
from datetime import datetime


class Memory:

    def __init__(self, path=None, max_items=100):
        self.max_items = max_items

        if path is None:
            root = Path(__file__).resolve().parents[2]
            path = root / "logs" / "memory.json"

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.items = []
        self.load()

    def load(self):
        if not self.path.exists():
            self.items = []
            return

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )

            self.items = data if isinstance(data, list) else []

        except Exception:
            self.items = []

    def save(self):
        try:
            self.path.write_text(
                json.dumps(
                    self.items[-self.max_items:],
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )
        except Exception:
            pass

    def add(self, role, content):
        self.items.append({
            "role": str(role),
            "content": str(content),
            "time": datetime.now().isoformat()
        })

        self.items = self.items[-self.max_items:]
        self.save()

    def remember(self, content):
        self.add("memory", content)

    def recent(self, limit=10):
        return self.items[-limit:]

    def search(self, query, limit=10):
        query = str(query).lower().strip()

        if not query:
            return []

        results = []

        for item in reversed(self.items):
            text = str(item.get("content", "")).lower()

            if query in text:
                results.append(item)

            if len(results) >= limit:
                break

        return results

    def clear(self):
        self.items = []
        self.save()

    def __len__(self):
        return len(self.items)
