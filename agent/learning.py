import json
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

LEARNING_DIR = BASE_DIR / "data" / "learning"
LEARNING_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DB_PATH = LEARNING_DIR / "learning.db"


def connect():
    return sqlite3.connect(str(DB_PATH))


def initialize():
    with connect() as con:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_request TEXT NOT NULL,
                action TEXT,
                arguments TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS successes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_request TEXT NOT NULL,
                action TEXT,
                result TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def record_failure(
    user_request,
    action="",
    arguments=None,
    error="",
):
    initialize()

    if arguments is None:
        arguments = {}

    with connect() as con:

        con.execute(
            """
            INSERT INTO failures(
                user_request,
                action,
                arguments,
                error,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_request,
                action,
                json.dumps(
                    arguments,
                    ensure_ascii=False
                ),
                str(error),
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )


def record_success(
    user_request,
    action="",
    result="",
):
    initialize()

    with connect() as con:

        con.execute(
            """
            INSERT INTO successes(
                user_request,
                action,
                result,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_request,
                action,
                str(result),
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )


def recent_failures(limit=20):

    initialize()

    with connect() as con:

        return con.execute(
            """
            SELECT
                user_request,
                action,
                arguments,
                error,
                created_at
            FROM failures
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


def recent_successes(limit=20):

    initialize()

    with connect() as con:

        return con.execute(
            """
            SELECT
                user_request,
                action,
                result,
                created_at
            FROM successes
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


def find_similar_failures(
    request,
    limit=5
):
    """
    Very lightweight experience lookup.

    This does not modify Python source code.
    It simply remembers previous failures and
    exposes relevant ones to the agent.
    """

    initialize()

    words = {
        word.lower()
        for word in request.split()
        if len(word) >= 4
    }

    rows = recent_failures(100)

    matches = []

    for row in rows:

        previous_request = str(
            row[0]
        ).lower()

        score = 0

        for word in words:

            if word in previous_request:
                score += 1

        if score > 0:

            matches.append(
                (score, row)
            )

    matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        row
        for _, row in matches[:limit]
    ]


def build_memory_context(
    request,
    limit=5
):

    rows = find_similar_failures(
        request,
        limit
    )

    if not rows:
        return ""

    parts = []

    for row in rows:

        parts.append(
            (
                "Previous failure:\n"
                f"Request: {row[0]}\n"
                f"Action: {row[1]}\n"
                f"Error: {row[3]}"
            )
        )

    return "\n\n".join(parts)