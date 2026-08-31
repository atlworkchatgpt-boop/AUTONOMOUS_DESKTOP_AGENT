import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "data" / "learning"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = MEMORY_DIR / "smart_memory.db"


def connect():
    return sqlite3.connect(str(DB_PATH))


def initialize():

    with connect() as con:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request TEXT NOT NULL,
                intent TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                success INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_request
            ON experiences(request)
            """
        )


def _short(value, maximum):

    value = str(value or "").strip()

    if len(value) > maximum:
        value = value[:maximum] + "..."

    return value


def remember(
    request,
    intent,
    action,
    result,
    success,
):

    initialize()

    request = _short(request, 400)
    intent = _short(intent, 100)
    action = _short(action, 150)
    result = _short(result, 800)

    with connect() as con:

        # Don't spam the database with identical events.
        existing = con.execute(
            """
            SELECT id
            FROM experiences
            WHERE request = ?
              AND intent = ?
              AND action = ?
              AND result = ?
              AND success = ?
            LIMIT 1
            """,
            (
                request,
                intent,
                action,
                result,
                int(bool(success)),
            )
        ).fetchone()

        if existing:
            return

        con.execute(
            """
            INSERT INTO experiences(
                request,
                intent,
                action,
                result,
                success,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request,
                intent,
                action,
                result,
                int(bool(success)),
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            )
        )


def recent(limit=20):

    initialize()

    with connect() as con:

        return con.execute(
            """
            SELECT
                request,
                intent,
                action,
                result,
                success,
                created_at
            FROM experiences
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit), 100)),)
        ).fetchall()


def relevant_context(
    request,
    limit=5,
):

    initialize()

    rows = recent(100)

    words = {
        word.lower()
        for word in str(request).split()
        if len(word) >= 4
    }

    if not words:
        return ""

    scored = []

    for row in rows:

        haystack = (
            row[0]
            + " "
            + row[1]
            + " "
            + row[2]
        ).lower()

        score = sum(
            1
            for word in words
            if word in haystack
        )

        if score:
            scored.append((score, row))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1][5],
        )
    )

    lines = []

    for _, row in scored[:limit]:

        state = (
            "SUCCESS"
            if row[4]
            else "FAILURE"
        )

        lines.append(
            f"[{state}] "
            f"{row[1]} -> {row[2]} -> {row[3]}"
        )

    return "\n".join(lines)


def statistics():

    initialize()

    with connect() as con:

        total = con.execute(
            "SELECT COUNT(*) FROM experiences"
        ).fetchone()[0]

        successful = con.execute(
            """
            SELECT COUNT(*)
            FROM experiences
            WHERE success = 1
            """
        ).fetchone()[0]

        failed = con.execute(
            """
            SELECT COUNT(*)
            FROM experiences
            WHERE success = 0
            """
        ).fetchone()[0]

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
    }


initialize()