import sqlite3


def migrate_guest_chat_schema(db_path):

    conn = sqlite3.connect(
        db_path,
        timeout=30,
        check_same_thread=False
    )

    try:

        columns = conn.execute(
            "PRAGMA table_info(chats)"
        ).fetchall()

        if not columns:
            return

        names = {row[1] for row in columns}

        if "guest_token_hash" not in names:

            conn.execute(
                "ALTER TABLE chats ADD COLUMN guest_token_hash TEXT"
            )

            print(
                "[DB] Added guest_token_hash"
            )

        user_row = None

        for row in columns:

            if row[1] == "user_id":
                user_row = row
                break

        needs_rebuild = (
            user_row is not None
            and int(user_row[3]) == 1
        )

        if needs_rebuild:

            conn.execute(
                "PRAGMA foreign_keys=OFF"
            )

            conn.execute(
                """
                CREATE TABLE chats_new (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    guest_token_hash TEXT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """
            )

            conn.execute(
                """
                INSERT INTO chats_new
                (
                    id,
                    user_id,
                    guest_token_hash,
                    title,
                    created_at,
                    updated_at
                )
                SELECT
                    id,
                    user_id,
                    guest_token_hash,
                    title,
                    created_at,
                    updated_at
                FROM chats
                """
            )

            conn.execute(
                "DROP TABLE chats"
            )

            conn.execute(
                "ALTER TABLE chats_new RENAME TO chats"
            )

            conn.execute(
                "PRAGMA foreign_keys=ON"
            )

            print(
                "[DB] Rebuilt chats table for guest support"
            )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chats_guest_token
            ON chats(guest_token_hash)
            """
        )

        conn.commit()

        print(
            "[DB] Guest chat schema ready"
        )

    finally:

        conn.close()
