import re
import sqlite3
from datetime import datetime, timezone


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


class MemoryStore:

    def __init__(self, db_path):
        self.db_path = db_path
        self._init()

    def _db(self):

        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False
        )

        conn.row_factory = sqlite3.Row

        conn.execute(
            "PRAGMA journal_mode=WAL"
        )

        return conn

    def _init(self):

        conn = self._db()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                memory TEXT NOT NULL,
                importance INTEGER NOT NULL DEFAULT 5,
                source_chat_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, memory)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_user
            ON memories(user_id)
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    def add(
        self,
        user_id,
        memory,
        category="general",
        importance=5,
        source_chat_id=None
    ):

        memory = str(memory).strip()

        if not memory:
            return None

        importance = max(
            1,
            min(
                10,
                int(importance)
            )
        )

        conn = self._db()

        existing = conn.execute(
            """
            SELECT id, importance
            FROM memories
            WHERE user_id = ?
              AND memory = ?
            """,
            (
                user_id,
                memory
            )
        ).fetchone()

        if existing:

            new_importance = max(
                existing["importance"],
                importance
            )

            conn.execute(
                """
                UPDATE memories
                SET importance = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    new_importance,
                    utc_now(),
                    existing["id"]
                )
            )

            conn.commit()
            conn.close()

            return existing["id"]

        cur = conn.execute(
            """
            INSERT INTO memories
            (
                user_id,
                category,
                memory,
                importance,
                source_chat_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                category,
                memory,
                importance,
                source_chat_id,
                utc_now(),
                utc_now()
            )
        )

        conn.commit()

        memory_id = cur.lastrowid

        conn.close()

        return memory_id

    # --------------------------------------------------------
    # ALL
    # --------------------------------------------------------

    def all(
        self,
        user_id
    ):

        conn = self._db()

        rows = conn.execute(
            """
            SELECT *
            FROM memories
            WHERE user_id = ?
            ORDER BY importance DESC, updated_at DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        return [
            dict(row)
            for row in rows
        ]

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def delete(
        self,
        user_id,
        memory_id
    ):

        conn = self._db()

        conn.execute(
            """
            DELETE FROM memories
            WHERE id = ?
              AND user_id = ?
            """,
            (
                memory_id,
                user_id
            )
        )

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    def clear(
        self,
        user_id
    ):

        conn = self._db()

        conn.execute(
            """
            DELETE FROM memories
            WHERE user_id = ?
            """,
            (user_id,)
        )

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # RELEVANT MEMORY SEARCH
    # --------------------------------------------------------

    def relevant(
        self,
        user_id,
        query,
        limit=8
    ):

        memories = self.all(
            user_id
        )

        if not memories:
            return []

        query_words = set(
            re.findall(
                r"[a-zA-Z0-9_]+",
                query.lower()
            )
        )

        scored = []

        for item in memories:

            memory_words = set(
                re.findall(
                    r"[a-zA-Z0-9_]+",
                    item["memory"].lower()
                )
            )

            overlap = len(
                query_words &
                memory_words
            )

            score = (
                overlap * 4
                + item["importance"]
            )

            if overlap > 0:
                scored.append(
                    (
                        score,
                        item
                    )
                )

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            item
            for _, item
            in scored[:limit]
        ]

    # --------------------------------------------------------
    # PROMPT BLOCK
    # --------------------------------------------------------

    def prompt_block(
        self,
        user_id,
        query
    ):

        relevant = self.relevant(
            user_id,
            query
        )

        if not relevant:
            return ""

        lines = [
            "Useful long-term memories about this user:"
        ]

        for item in relevant:

            lines.append(
                "- "
                + item["memory"]
            )

        return "\n".join(
            lines
        )


# ============================================================
# SIMPLE MEMORY EXTRACTION
# ============================================================

def extract_memories(
    message
):

    text = str(
        message
    ).strip()

    memories = []

    patterns = [

        (
            r"\bmy name is ([A-Za-z][A-Za-z0-9 _-]{1,40})",
            "identity",
            9,
        ),

        (
            r"\bcall me ([A-Za-z][A-Za-z0-9 _-]{1,40})",
            "identity",
            9,
        ),

        (
            r"\bi use ([^.!?\n]{2,80})",
            "preferences",
            7,
        ),

        (
            r"\bi prefer ([^.!?\n]{2,100})",
            "preferences",
            8,
        ),

        (
            r"\bi like ([^.!?\n]{2,100})",
            "preferences",
            6,
        ),

        (
            r"\bi don't like ([^.!?\n]{2,100})",
            "preferences",
            7,
        ),

        (
            r"\bi am using ([^.!?\n]{2,100})",
            "environment",
            7,
        ),

        (
            r"\bi work on ([^.!?\n]{2,120})",
            "projects",
            8,
        ),

        (
            r"\bmy project is ([^.!?\n]{2,120})",
            "projects",
            8,
        ),

        (
            r"\bi am building ([^.!?\n]{2,120})",
            "projects",
            8,
        ),

        (
            r"\bi live in ([^.!?\n]{2,100})",
            "general",
            5,
        ),
    ]

    for pattern, category, importance in patterns:

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):

            value = match.group(1).strip()

            value = re.sub(
                r"\s+",
                " ",
                value
            )

            if value:

                memories.append(
                    {
                        "category": category,
                        "memory": (
                            f"User said: {value}"
                        ),
                        "importance": importance
                    }
                )

    return memories
