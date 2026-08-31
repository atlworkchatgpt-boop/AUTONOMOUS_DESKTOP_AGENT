import sqlite3
from datetime import datetime

from config.config import DB_PATH


def connect():

    return sqlite3.connect(
        DB_PATH
    )


def initialize():

    with connect() as con:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT,
                content TEXT,
                created_at TEXT
            )
            """
        )


def add_event(
    kind,
    content,
):

    initialize()

    with connect() as con:

        con.execute(
            """
            INSERT INTO events(
                kind,
                content,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                kind,
                content,
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            ),
        )


def recent_events(
    limit=100,
):

    initialize()

    with connect() as con:

        return con.execute(
            """
            SELECT kind, content, created_at
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                limit,
            ),
        ).fetchall()