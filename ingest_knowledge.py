import os

from agent.memory.rag import KnowledgeBase


def ingest():

    db = KnowledgeBase()

    count = 0

    for root, dirs, files in os.walk(
        "knowledge"
    ):

        for filename in files:

            if not filename.lower().endswith(
                ".txt"
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
                ) as file:

                    text = file.read()

                if text.strip():

                    db.add_text(
                        text,
                        source=path
                    )

                    count += 1

                    print(
                        "[+] Added:",
                        path
                    )

            except Exception as e:

                print(
                    "[!] Failed:",
                    path,
                    e
                )

    print()
    print(
        "[+] Ingested",
        count,
        "document(s)."
    )


if __name__ == "__main__":

    ingest()
