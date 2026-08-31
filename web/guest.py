import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")


def now():
    return datetime.now(timezone.utc).isoformat()


def token_hash(token: str):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def get_db_path():
    from web.main import DB_PATH
    return DB_PATH


def init_guest_tables():

    conn = sqlite3.connect(
        get_db_path(),
        timeout=30,
        check_same_thread=False
    )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS guest_sessions (
            token_hash TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_guest_token():

    init_guest_tables()

    token = secrets.token_urlsafe(48)

    created = datetime.now(
        timezone.utc
    )

    expires = (
        created +
        timedelta(hours=24)
    )

    conn = sqlite3.connect(
        get_db_path(),
        timeout=30
    )

    conn.execute(
        """
        INSERT INTO guest_sessions
        (
            token_hash,
            created_at,
            expires_at
        )
        VALUES (?, ?, ?)
        """,
        (
            token_hash(token),
            created.isoformat(),
            expires.isoformat()
        )
    )

    conn.commit()
    conn.close()

    return token


def valid_guest(request: Request):

    init_guest_tables()

    token = request.cookies.get(
        "autonomous_guest"
    )

    if not token:
        return False

    conn = sqlite3.connect(
        get_db_path(),
        timeout=30
    )

    row = conn.execute(
        """
        SELECT token_hash
        FROM guest_sessions
        WHERE token_hash = ?
        AND expires_at > ?
        """,
        (
            token_hash(token),
            now()
        )
    ).fetchone()

    conn.close()

    return row is not None


@router.post("/guest")
async def guest_login():

    token = create_guest_token()

    response = JSONResponse(
        {
            "ok": True,
            "guest": True
        }
    )

    response.set_cookie(
        key="autonomous_guest",
        value=token,
        max_age=60 * 60 * 24,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response


@router.get("/guest/status")
async def guest_status(
    request: Request
):

    return {
        "guest": valid_guest(request)
    }


@router.post("/guest/logout")
async def guest_logout(
    request: Request
):

    token = request.cookies.get(
        "autonomous_guest"
    )

    if token:

        conn = sqlite3.connect(
            get_db_path(),
            timeout=30
        )

        conn.execute(
            """
            DELETE FROM guest_sessions
            WHERE token_hash = ?
            """,
            (
                token_hash(token),
            )
        )

        conn.commit()
        conn.close()

    response = JSONResponse(
        {
            "ok": True
        }
    )

    response.delete_cookie(
        "autonomous_guest"
    )

    return response
