import os
import re


class KnowledgeBase:

    def __init__(self):

        self.documents = []

        self.load()

    def load(self):

        self.documents = []

        base = os.path.abspath("knowledge")

        if not os.path.exists(base):
            return

        for root, dirs, files in os.walk(base):

            for filename in files:

                if not filename.lower().endswith(
                    (".txt", ".md")
                ):
                    continue

                path = os.path.join(
                    root,
                    filename
                )

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8",
                        errors="replace"
                    ) as f:

                        text = f.read()

                    if text.strip():

                        self.documents.append(
                            {
                                "path": path,
                                "text": text
                            }
                        )

                except Exception:
                    pass

    def words(self, text):

        return set(
            re.findall(
                r"[a-zA-Z0-9_]+",
                text.lower()
            )
        )

    def search(self, query, limit=3):

        query_words = self.words(query)

        if not query_words:
            return []

        scored = []

        for doc in self.documents:

            doc_words = self.words(
                doc["text"]
            )

            overlap = len(
                query_words & doc_words
            )

            if overlap > 0:

                score = overlap / max(
                    len(query_words),
                    1
                )

                scored.append(
                    (
                        score,
                        doc
                    )
                )

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            {
                "text": item["text"],
                "source": item["path"],
                "score": score
            }
            for score, item in scored[:limit]
        ]

    def build_context(self, query, limit=3):

        results = self.search(
            query,
            limit
        )

        if not results:
            return ""

        output = []

        for item in results:

            output.append(
                "[SOURCE: "
                + item["source"]
                + "]\n"
                + item["text"]
            )

        return "\n\n".join(output)

    def add_text(self, text, source="manual"):

        if not text.strip():
            return False

        self.documents.append(
            {
                "path": source,
                "text": text
            }
        )

        return True
