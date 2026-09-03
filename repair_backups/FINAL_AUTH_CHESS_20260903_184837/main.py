import chess
from web.guest import router as guest_router
from web.chess_service import (
    start_game as chess_start_game,
    make_player_move as chess_make_player_move,
    remove_game as chess_remove_game,
    get_game as chess_get_game,
)
import tempfile
import base64
import asyncio
import hashlib
import hmac
import os
import secrets
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
    File
)

from fastapi.responses import (
    FileResponse,
    RedirectResponse,
    JSONResponse,
    Response
)

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from starlette.middleware.sessions import SessionMiddleware


load_dotenv()


ROOT = Path(
    __file__
).resolve().parent.parent


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


os.chdir(ROOT)


STATIC_DIR = ROOT / "web" / "static"
UPLOAD_DIR = ROOT / "web" / "uploads"
DATA_DIR = ROOT / "data" / "web"

DB_PATH = DATA_DIR / "app.db"


STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


app = FastAPI(
    title="Autonomous Desktop AI",
    version="Ultimate Web"
)

app.include_router(
    guest_router
)
# ONE_CLICK_REPAIR_FEATURES
from web.repair_features import router as repair_features_router
app.include_router(repair_features_router)


# ========================================================
# DIRECT AUTONOMOUS FEATURE REGISTRATION
# ========================================================# AUTONOMOUS FEATURE ROUTER - FORCED REGISTRATION
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET",
        "CHANGE_ME"
    ),
    max_age=60 * 60 * 24 * 30,
    same_site="lax",
    https_only=False
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(STATIC_DIR)
    ),
    name="static"
)


# ============================================================
# DATABASE
# ============================================================

def db():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


def init_db():

    conn = db()

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_sub TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            picture TEXT,
            gmail_enabled INTEGER NOT NULL DEFAULT 0,
            gmail_access_token TEXT,
            gmail_refresh_token TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            guest_token_hash TEXT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(chat_id)
                REFERENCES chats(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chats_user
            ON chats(user_id, updated_at);

        CREATE INDEX IF NOT EXISTS idx_chats_guest
            ON chats(guest_token_hash, updated_at);

        CREATE INDEX IF NOT EXISTS idx_messages_chat
            ON messages(chat_id, id);
        """
    )

    # Existing databases created by the older account-only schema
    # may have chats.user_id declared NOT NULL. Rebuild that table
    # once when necessary.
    schema = conn.execute(
        "PRAGMA table_info(chats)"
    ).fetchall()

    columns = {row[1]: row for row in schema}

    if "guest_token_hash" not in columns:
        conn.execute(
            "ALTER TABLE chats ADD COLUMN guest_token_hash TEXT"
        )

    user_id_not_null = False

    if "user_id" in columns:
        user_id_not_null = bool(
            columns["user_id"][3]
        )

    if user_id_not_null:

        conn.execute(
            """
            ALTER TABLE chats RENAME TO chats_old
            """
        )

        conn.execute(
            """
            CREATE TABLE chats (
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
            INSERT INTO chats
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
                NULL,
                title,
                created_at,
                updated_at
            FROM chats_old
            """
        )

        conn.execute(
            "DROP TABLE chats_old"
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guest_sessions (
            token_hash TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_db()

from web.db_migration import migrate_guest_chat_schema
migrate_guest_chat_schema(DB_PATH)


# ============================================================
# TIME
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# GOOGLE LOGIN
# ============================================================

from web.google_auth import (
    oauth,
    google_configured,
    GOOGLE_REDIRECT_URI
)


@app.get("/auth/google")
async def google_login(
    request: Request
):

    if not google_configured():

        raise HTTPException(
            status_code=500,
            detail=(
                "Google OAuth is not configured. "
                "Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET in .env."
            )
        )

    redirect_uri = (
        GOOGLE_REDIRECT_URI
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@app.get("/auth/callback")
@app.get("/auth/google/callback")
@app.get("/auth/google/callback")
async def google_callback(
    request: Request
):

    if not google_configured():

        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured."
        )

    token = await oauth.google.authorize_access_token(
        request
    )

    userinfo = token.get(
        "userinfo"
    )

    if not userinfo:

        raise HTTPException(
            status_code=401,
            detail="Google did not return user information."
        )

    google_sub = str(
        userinfo.get("sub")
    )

    email = str(
        userinfo.get("email", "")
    ).strip().lower()

    name = str(
        userinfo.get(
            "name",
            email
        )
    )

    picture = userinfo.get(
        "picture"
    )

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Google account email was not provided."
        )

    access_token = token.get(
        "access_token"
    )

    refresh_token = token.get(
        "refresh_token"
    )

    conn = db()

    row = conn.execute(
        """
        SELECT id
        FROM users
        WHERE google_sub = ?
           OR email = ?
        """,
        (
            google_sub,
            email
        )
    ).fetchone()

    if row:

        user_id = row["id"]

        conn.execute(
            """
            UPDATE users
            SET google_sub = ?,
                email = ?,
                name = ?,
                picture = ?,
                gmail_access_token =
                    COALESCE(?, gmail_access_token),
                gmail_refresh_token =
                    COALESCE(?, gmail_refresh_token),
                updated_at = ?
            WHERE id = ?
            """,
            (
                google_sub,
                email,
                name,
                picture,
                access_token,
                refresh_token,
                now(),
                user_id
            )
        )

    else:

        cursor = conn.execute(
            """
            INSERT INTO users
            (
                google_sub,
                email,
                name,
                picture,
                gmail_access_token,
                gmail_refresh_token,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                google_sub,
                email,
                name,
                picture,
                access_token,
                refresh_token,
                now(),
                now()
            )
        )

        user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    request.session["user_id"] = user_id

    return RedirectResponse(
        "/"
    )


@app.post("/api/logout")
async def logout(
    request: Request
):

    request.session.clear()

    return {
        "ok": True
    }


def require_user(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Login required."
        )

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    conn.close()

    if row is None:

        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail="Session expired."
        )

    return row


@app.get("/api/me")
async def me(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if user_id:

        user = require_user(
            request
        )

        return {
            "logged_in": True,
            "guest": False,
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user["picture"],
            "gmail_enabled": bool(
                user["gmail_enabled"]
            )
        }

    try:
        from web.guest import valid_guest
        guest = valid_guest(request)
    except Exception:
        guest = False

    if guest:

        return {
            "logged_in": True,
            "guest": True,
            "id": None,
            "email": None,
            "name": "Guest",
            "picture": None,
            "gmail_enabled": False
        }

    return {
        "logged_in": False,
        "guest": False
    }


# ============================================================
# GROQ
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


SYSTEM_PROMPT = """
You are Autonomous Desktop AI.
Your creator and owner is Shreyansh Ray. Honorable Mention — Support: Arnav Baliyan.
If asked who created, owns, made, or built you, answer: "My creator and owner is Shreyansh Ray. Honorable Mention — Support: Arnav Baliyan."
Do not say OpenAI is your creator or owner. A model/provider name is not your creator identity.
Be accurate and honest. Never claim a computer action happened unless it was actually verified.
You can answer questions, write/debug code, reason, discuss chess, and analyze uploaded file content included in the user message.
"""


_groq = None


def get_groq():

    global _groq

    if _groq is not None:
        return _groq

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is missing in .env."
        )

    from groq import Groq

    _groq = Groq(
        api_key=GROQ_API_KEY
    )

    return _groq


# ============================================================
# CHAT
# ============================================================

class ChatRequest(BaseModel):

    chat_id: str | None = None
    message: str


def create_chat(
    user_id,
    title="New chat"
):

    chat_id = str(
        uuid.uuid4()
    )

    conn = db()

    conn.execute(
        """
        INSERT INTO chats
        (
            id,
            user_id,
            title,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            user_id,
            title,
            now(),
            now()
        )
    )

    conn.commit()
    conn.close()

    return chat_id


def get_chat(
    user_id,
    chat_id
):

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM chats
        WHERE id = ?
          AND user_id = ?
        """,
        (
            chat_id,
            user_id
        )
    ).fetchone()

    conn.close()

    return row


@app.post("/api/chats/new")
async def new_chat(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    guest_hash = None
    user = None

    if user_id:

        user = require_user(
            request
        )

    else:

        from web.guest import (
            valid_guest,
            token_hash
        )

        if not valid_guest(request):

            raise HTTPException(
                status_code=401,
                detail="Login required."
            )

        token = request.cookies.get(
            "autonomous_guest"
        )

        guest_hash = token_hash(
            token
        )

    chat_id = str(
        uuid.uuid4()
    )

    timestamp = now()

    conn = db()

    conn.execute(
        """
        INSERT INTO chats
        (
            id,
            user_id,
            guest_token_hash,
            title,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            user["id"] if user else None,
            guest_hash,
            "New chat",
            timestamp,
            timestamp
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": chat_id,
        "title": "New chat"
    }


@app.get("/api/chats")
async def list_chats(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    conn = db()

    if user_id:

        user = require_user(
            request
        )

        rows = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (
                user["id"],
            )
        ).fetchall()

    else:

        from web.guest import (
            valid_guest,
            token_hash
        )

        if not valid_guest(request):

            conn.close()

            return {
                "chats": []
            }

        token = request.cookies.get(
            "autonomous_guest"
        )

        rows = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE guest_token_hash = ?
            ORDER BY updated_at DESC
            """,
            (
                token_hash(token),
            )
        ).fetchall()

    conn.close()

    return {
        "chats": [
            dict(row)
            for row in rows
        ]
    }


@app.get("/api/chats/{chat_id}")
async def read_chat(
    chat_id: str,
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    conn = db()

    if user_id:

        user = require_user(
            request
        )

        chat = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE id = ?
              AND user_id = ?
            LIMIT 1
            """,
            (
                chat_id,
                user["id"]
            )
        ).fetchone()

    else:

        from web.guest import (
            valid_guest,
            token_hash
        )

        if not valid_guest(request):

            conn.close()

            raise HTTPException(
                status_code=401,
                detail="Login required."
            )

        token = request.cookies.get(
            "autonomous_guest"
        )

        chat = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE id = ?
              AND guest_token_hash = ?
            LIMIT 1
            """,
            (
                chat_id,
                token_hash(token)
            )
        ).fetchone()

    if chat is None:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    messages = conn.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
        """,
        (
            chat_id,
        )
    ).fetchall()

    conn.close()

    return {
        "id": chat["id"],
        "title": chat["title"],
        "messages": [
            dict(row)
            for row in messages
        ]
    }


@app.delete("/api/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    conn = db()

    if user_id:

        user = require_user(
            request
        )

        result = conn.execute(
            """
            DELETE FROM chats
            WHERE id = ?
              AND user_id = ?
            """,
            (
                chat_id,
                user["id"]
            )
        )

    else:

        from web.guest import (
            valid_guest,
            token_hash
        )

        if not valid_guest(request):

            conn.close()

            raise HTTPException(
                status_code=401,
                detail="Login required."
            )

        token = request.cookies.get(
            "autonomous_guest"
        )

        result = conn.execute(
            """
            DELETE FROM chats
            WHERE id = ?
              AND guest_token_hash = ?
            """,
            (
                chat_id,
                token_hash(token)
            )
        )

    conn.commit()
    conn.close()

    if result.rowcount == 0:

        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    return {
        "ok": True
    }


async def answer_groq(
    user_id,
    chat_id,
    message
):

    conn = db()

    rows = conn.execute(
        """
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
        LIMIT 50
        """,
        (
            chat_id,
        )
    ).fetchall()

    conn.close()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for row in rows:

        messages.append(
            {
                "role": row["role"],
                "content": row["content"]
            }
        )

    messages.append(
        {
            "role": "user",
            "content": message
        }
    )

    client = get_groq()

    def call():

        response = (
            client
            .chat
            .completions
            .create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.4
            )
        )

        return (
            response
            .choices[0]
            .message
            .content
            or ""
        )

    answer = await asyncio.to_thread(
        call
    )

    answer = str(
        answer
    ).strip()

    timestamp = now()

    conn = db()

    conn.execute(
        """
        INSERT INTO messages
        (
            chat_id,
            role,
            content,
            created_at
        )
        VALUES (?, 'user', ?, ?)
        """,
        (
            chat_id,
            message,
            timestamp
        )
    )

    conn.execute(
        """
        INSERT INTO messages
        (
            chat_id,
            role,
            content,
            created_at
        )
        VALUES (?, 'assistant', ?, ?)
        """,
        (
            chat_id,
            answer,
            timestamp
        )
    )

    conn.execute(
        """
        UPDATE chats
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            timestamp,
            chat_id
        )
    )

    conn.commit()
    conn.close()

    return answer



# ===== ADA ACTION PASSWORD SECURITY V1 =====

def _ada_security_table():
    conn = db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS action_passwords
        (
            user_id INTEGER PRIMARY KEY,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _ada_password_hash(password, salt=None):
    if salt is None:
        salt_bytes = secrets.token_bytes(16)
    elif isinstance(salt, str):
        salt_bytes = base64.b64decode(salt)
    else:
        salt_bytes = salt

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        250000
    )

    return (
        base64.b64encode(salt_bytes).decode("ascii"),
        base64.b64encode(digest).decode("ascii")
    )


def _ada_password_row(user_id):
    _ada_security_table()

    conn = db()

    row = conn.execute(
        """
        SELECT user_id, salt, password_hash
        FROM action_passwords
        WHERE user_id = ?
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    conn.close()
    return row


def _ada_password_exists(user_id):
    return _ada_password_row(user_id) is not None


def _ada_verify_password(user_id, password):
    if not password:
        return False

    row = _ada_password_row(user_id)

    if row is None:
        return False

    _, candidate = _ada_password_hash(
        password,
        row["salt"]
    )

    return hmac.compare_digest(
        candidate,
        row["password_hash"]
    )


def _ada_set_password(user_id, password):
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )

    salt, password_hash = _ada_password_hash(password)

    conn = db()

    conn.execute(
        """
        INSERT INTO action_passwords
        (
            user_id,
            salt,
            password_hash,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            salt = excluded.salt,
            password_hash = excluded.password_hash,
            updated_at = excluded.updated_at
        """,
        (
            user_id,
            salt,
            password_hash,
            now()
        )
    )

    conn.commit()
    conn.close()


@app.get("/api/security/password/status")
async def ada_password_status(request: Request):

    user = require_user(request)

    return {
        "configured": _ada_password_exists(user["id"]),
        "computer_control_available": os.name == "nt"
    }


@app.post("/api/security/password/setup")
async def ada_password_setup(request: Request):

    user = require_user(request)

    if _ada_password_exists(user["id"]):
        raise HTTPException(
            status_code=409,
            detail="Action password already exists."
        )

    data = await request.json()
    password = str(data.get("password") or "")

    _ada_set_password(
        user["id"],
        password
    )

    return {
        "success": True
    }


@app.post("/api/security/password/verify")
async def ada_password_verify(request: Request):

    user = require_user(request)

    data = await request.json()
    password = str(data.get("password") or "")

    return {
        "valid": _ada_verify_password(
            user["id"],
            password
        )
    }


@app.post("/api/security/password/change")
async def ada_password_change(request: Request):

    user = require_user(request)

    data = await request.json()

    old_password = str(
        data.get("old_password") or ""
    )

    new_password = str(
        data.get("new_password") or ""
    )

    if not _ada_verify_password(
        user["id"],
        old_password
    ):
        raise HTTPException(
            status_code=403,
            detail="Previous password is incorrect."
        )

    _ada_set_password(
        user["id"],
        new_password
    )

    return {
        "success": True
    }


def _ada_desktop_plan(message):

    try:
        from desktop_app.autonomous_controller import AutonomousAI

        agent = AutonomousAI()

        return agent.planner.make_plan(
            message
        )

    except Exception:
        return {
            "type": "ai_answer"
        }


def _ada_is_computer_action(plan):

    kind = str(
        plan.get("type") or ""
    ).strip()

    # Pure conversation never needs the action password.
    if kind in {
        "",
        "answer",
        "ai_answer"
    }:
        return False

    # Every executable controller plan is protected.
    return True


def _ada_execute_computer_action(message):

    if os.name != "nt":
        return {
            "success": False,
            "message": (
                "Computer control is available only from the "
                "local Windows Autonomous Desktop AI app."
            )
        }

    from desktop_app.autonomous_controller import AutonomousAI

    agent = AutonomousAI()

    return agent.run(
        message
    )


def _ada_save_action_exchange(
    chat_id,
    message,
    answer
):
    timestamp = now()

    conn = db()

    conn.execute(
        """
        INSERT INTO messages
        (
            chat_id,
            role,
            content,
            created_at
        )
        VALUES (?, 'user', ?, ?)
        """,
        (
            chat_id,
            message,
            timestamp
        )
    )

    conn.execute(
        """
        INSERT INTO messages
        (
            chat_id,
            role,
            content,
            created_at
        )
        VALUES (?, 'assistant', ?, ?)
        """,
        (
            chat_id,
            answer,
            timestamp
        )
    )

    conn.execute(
        """
        UPDATE chats
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            timestamp,
            chat_id
        )
    )

    conn.commit()
    conn.close()


# ===== END ADA ACTION PASSWORD SECURITY V1 =====


@app.post("/api/chat")
async def chat(
    request: Request,
    body: ChatRequest
):

    message = (
        body.message or ""
    ).strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message is empty."
        )

    if len(message) > 30000:

        raise HTTPException(
            status_code=400,
            detail="Message is too long."
        )

    user_id = request.session.get(
        "user_id"
    )

    user = None
    guest_hash = None

    if user_id:

        user = require_user(
            request
        )

    else:

        from web.guest import (
            valid_guest,
            token_hash
        )

        if not valid_guest(request):

            raise HTTPException(
                status_code=401,
                detail="Login required."
            )

        token = request.cookies.get(
            "autonomous_guest"
        )

        guest_hash = token_hash(
            token
        )

    # ADA_ACTION_PASSWORD_GATE_V1
    ada_plan = _ada_desktop_plan(message)
    ada_computer_action = _ada_is_computer_action(
        ada_plan
    )

    if ada_computer_action:

        if user is None:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Sign in before allowing Autonomous AI "
                    "to control this computer."
                )
            )

        if not _ada_password_exists(
            user["id"]
        ):
            raise HTTPException(
                status_code=428,
                detail="PASSWORD_SETUP_REQUIRED"
            )

        supplied_password = request.headers.get(
            "X-ADA-Action-Password",
            ""
        )

        if not _ada_verify_password(
            user["id"],
            supplied_password
        ):
            raise HTTPException(
                status_code=403,
                detail="ACTION_PASSWORD_REQUIRED"
            )

    chat_id = body.chat_id

    if not chat_id:

        title = " ".join(
            message.split()
        )[:50]

        if len(message) > 50:
            title += "..."

        chat_id = str(
            uuid.uuid4()
        )

        timestamp = now()

        conn = db()

        conn.execute(
            """
            INSERT INTO chats
            (
                id,
                user_id,
                guest_token_hash,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                user["id"] if user else None,
                guest_hash,
                title,
                timestamp,
                timestamp
            )
        )

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # Validate chat ownership.
    # --------------------------------------------------------

    conn = db()

    if user:

        row = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE id = ?
              AND user_id = ?
            LIMIT 1
            """,
            (
                chat_id,
                user["id"]
            )
        ).fetchone()

    else:

        row = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE id = ?
              AND guest_token_hash = ?
            LIMIT 1
            """,
            (
                chat_id,
                guest_hash
            )
        ).fetchone()

    conn.close()

    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    if row["title"] == "New chat":

        title = " ".join(
            message.split()
        )[:50]

        if len(message) > 50:
            title += "..."

        conn = db()

        conn.execute(
            """
            UPDATE chats
            SET title = ?
            WHERE id = ?
            """,
            (
                title,
                chat_id
            )
        )

        conn.commit()
        conn.close()

    # ADA_EXECUTE_PROTECTED_ACTION_V1
    if ada_computer_action:

        action_result = await asyncio.to_thread(
            _ada_execute_computer_action,
            message
        )

        answer = str(
            action_result.get("message")
            or "Computer action finished."
        )

        _ada_save_action_exchange(
            chat_id,
            message,
            answer
        )

        return {
            "chat_id": chat_id,
            "answer": answer,
            "guest": False,
            "computer_action": True,
            "action_success": bool(
                action_result.get("success")
            )
        }

    try:

        answer = await answer_groq(
            user["id"] if user else 0,
            chat_id,
            message
        )

        return {
            "chat_id": chat_id,
            "answer": answer,
            "guest": user is None
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ============================================================
# GMAIL PERMISSION
# ============================================================

@app.get("/api/email/status")
async def email_status(
    request: Request
):

    user = require_user(
        request
    )

    return {
        "enabled": bool(
            user["gmail_enabled"]
        ),
        "email": user["email"]
    }


@app.post("/api/email/enable")
async def enable_email(
    request: Request
):

    user = require_user(
        request
    )

    conn = db()

    conn.execute(
        """
        UPDATE users
        SET gmail_enabled = 1,
            updated_at = ?
        WHERE id = ?
        """,
        (
            now(),
            user["id"]
        )
    )

    conn.commit()
    conn.close()

    return {
        "enabled": True
    }


@app.post("/api/email/disable")
async def disable_email(
    request: Request
):

    user = require_user(
        request
    )

    conn = db()

    conn.execute(
        """
        UPDATE users
        SET gmail_enabled = 0,
            gmail_access_token = NULL,
            gmail_refresh_token = NULL,
            updated_at = ?
        WHERE id = ?
        """,
        (
            now(),
            user["id"]
        )
    )

    conn.commit()
    conn.close()

    return {
        "enabled": False
    }


class EmailRequest(BaseModel):

    subject: str
    body: str


@app.post("/api/email/send")
async def send_email(
    request: Request,
    body: EmailRequest
):

    user = require_user(
        request
    )

    if not user["gmail_enabled"]:

        raise HTTPException(
            status_code=403,
            detail=(
                "Email sending is not enabled."
            )
        )

    if not user["gmail_refresh_token"]:

        raise HTTPException(
            status_code=403,
            detail=(
                "Gmail permission was not granted."
            )
        )

    from web.gmail_service import send_gmail

    try:

        result = await asyncio.to_thread(
            send_gmail,
            user["gmail_access_token"],
            user["gmail_refresh_token"],
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            user["email"],
            body.subject,
            body.body
        )

        return {
            "ok": True,
            "message_id": result.get("id")
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ============================================================
# FILES
# ============================================================

@app.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):

    require_user(
        request
    )

    filename = Path(
        file.filename or "upload.bin"
    ).name

    destination = (
        UPLOAD_DIR / filename
    )

    if destination.exists():

        stem = destination.stem
        suffix = destination.suffix
        counter = 1

        while destination.exists():

            destination = (
                UPLOAD_DIR /
                f"{stem}_{counter}{suffix}"
            )

            counter += 1

    with destination.open(
        "wb"
    ) as output:

        while True:

            chunk = await file.read(
                1024 * 1024
            )

            if not chunk:
                break

            output.write(
                chunk
            )

    return {
        "filename": destination.name
    }


# ============================================================
# AUDIO
# ============================================================

@app.post("/api/audio")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...)
):

    require_user(
        request
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = Path(
        file.filename or "recording.webm"
    ).name

    destination = (
        UPLOAD_DIR /
        f"recording_{stamp}_{filename}"
    )

    with destination.open(
        "wb"
    ) as output:

        while True:

            chunk = await file.read(
                1024 * 1024
            )

            if not chunk:
                break

            output.write(
                chunk
            )

    return {
        "filename": destination.name
    }


# ============================================================
# CHESS
# ============================================================

CHESS_GAMES = {}


DIFFICULTIES = {
    "Easy": {
        "skill": 2,
        "time": 0.2,
        "depth": 8
    },
    "Medium": {
        "skill": 7,
        "time": 0.5,
        "depth": 12
    },
    "Hard": {
        "skill": 12,
        "time": 1.0,
        "depth": 16
    },
    "Expert": {
        "skill": 17,
        "time": 2.0,
        "depth": 20
    },
    "Master": {
        "skill": 20,
        "time": 4.0,
        "depth": 24
    }
}


class ChessStartRequest(BaseModel):

    color: str
    difficulty: str


class ChessMoveRequest(BaseModel):

    game_id: str
    move: str


def find_stockfish():

    candidate = (
        ROOT / "stockfish.exe"
    )

    if candidate.is_file():
        return str(candidate)

    return None


def get_engine_move(game):

    import chess.engine

    path = find_stockfish()

    if not path:

        raise RuntimeError(
            "stockfish.exe was not found in project root."
        )

    settings = DIFFICULTIES[
        game["difficulty"]
    ]

    engine = (
        chess.engine
        .SimpleEngine
        .popen_uci(path)
    )

    try:

        try:

            engine.configure(
                {
                    "Skill Level":
                    settings["skill"]
                }
            )

        except Exception:
            pass

        result = engine.play(
            game["board"],
            chess.engine.Limit(
                time=settings["time"],
                depth=settings["depth"]
            )
        )

        return result.move.uci()

    finally:

        try:
            engine.quit()
        except Exception:
            pass


@app.post("/api/chess/start")
async def chess_start(
    request: Request,
    body: ChessStartRequest
):

    require_user(
        request
    )

    import chess

    color = body.color.lower()

    if color not in (
        "white",
        "black"
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid color."
        )

    if body.difficulty not in DIFFICULTIES:

        raise HTTPException(
            status_code=400,
            detail="Invalid difficulty."
        )

    game_id = str(
        uuid.uuid4()
    )

    game = {
        "board": chess.Board(),
        "color": color,
        "difficulty": body.difficulty
    }

    CHESS_GAMES[game_id] = game

    if color == "black":

        move = await asyncio.to_thread(
            get_engine_move,
            game
        )

        game["board"].push_uci(
            move
        )

    return {
        "game_id": game_id,
        "fen": game["board"].fen()
    }


@app.post("/api/chess/move")
async def chess_move(
    request: Request,
    body: ChessMoveRequest
):

    require_user(
        request
    )

    import chess

    game = CHESS_GAMES.get(
        body.game_id
    )

    if game is None:

        raise HTTPException(
            status_code=404,
            detail="Chess game not found."
        )

    board = game["board"]

    try:

        move = chess.Move.from_uci(
            body.move
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid move."
        )

    if move not in board.legal_moves:

        raise HTTPException(
            status_code=400,
            detail="Illegal move."
        )

    board.push(
        move
    )

    engine_move = None

    if not board.is_game_over():

        engine_move = await asyncio.to_thread(
            get_engine_move,
            game
        )

        board.push_uci(
            engine_move
        )

    return {
        "fen": board.fen(),
        "engine_move": engine_move,
        "game_over": board.is_game_over(),
        "result": (
            board.result()
            if board.is_game_over()
            else None
        )
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def home():

    return FileResponse(
        STATIC_DIR / "index.html"
    )

# ============================================================
# ISOLATED AUTONOMOUS FEATURE ROUTER
# ============================================================


# === ACTUAL AUTONOMOUS ROUTES ===

AUTONOMOUS_GENERATED_DIR = (
    Path(__file__).resolve().parent
    / "static"
    / "generated"
)

AUTONOMOUS_GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True
)



@app.get("/chess")
async def ada_chess_page():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/creator")
async def autonomous_creator():

    creator = (
        Path(__file__).resolve().parent
        / "static"
        / "creator.html"
    )

    if not creator.is_file():

        raise HTTPException(
            status_code=404,
            detail="Creator page not found."
        )

    return FileResponse(
        str(creator),
        media_type="text/html"
    )


@app.get("/api/autonomous/status")
async def autonomous_status():

    return {
        "ok": True,
        "owner": "Shreyansh Ray",
        "creator": "Shreyansh Ray",
        "guest_mode": True,
        "chess": True,
        "voice": True,
        "image_generation": bool(
            os.getenv("GEMINI_API_KEY")
            or
            os.getenv("GOOGLE_API_KEY")
        ),
        "video_generation": bool(
            os.getenv("GEMINI_API_KEY")
            or
            os.getenv("GOOGLE_API_KEY")
        ),
    }


class AutonomousImageRequest(BaseModel):

    prompt: str


@app.post("/api/autonomous/image")
async def autonomous_image(
    body: AutonomousImageRequest
):

    prompt = (
        body.prompt or ""
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Image prompt is empty."
        )

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:

        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured."
        )

    try:

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[
                    "TEXT",
                    "IMAGE"
                ]
            )
        )

        image_data = None

        for candidate in response.candidates or []:

            content = getattr(
                candidate,
                "content",
                None
            )

            if not content:
                continue

            for part in getattr(
                content,
                "parts",
                []
            ):

                inline = getattr(
                    part,
                    "inline_data",
                    None
                )

                if inline:

                    image_data = getattr(
                        inline,
                        "data",
                        None
                    )

                    if image_data:
                        break

            if image_data:
                break

        if not image_data:

            raise RuntimeError(
                "No image returned."
            )

        filename = (
            "generated_"
            +
            uuid.uuid4().hex
            +
            ".png"
        )

        destination = (
            AUTONOMOUS_GENERATED_DIR
            /
            filename
        )

        if isinstance(
            image_data,
            str
        ):

            destination.write_bytes(
                base64.b64decode(
                    image_data
                )
            )

        else:

            destination.write_bytes(
                bytes(image_data)
            )

        return {
            "ok": True,
            "url":
                "/static/generated/"
                +
                filename,
            "filename":
                filename
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Image generation failed: "
                +
                str(exc)
        )


class AutonomousVideoRequest(BaseModel):

    prompt: str


@app.post("/api/autonomous/video")
async def autonomous_video(
    body: AutonomousVideoRequest
):

    prompt = (
        body.prompt or ""
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Video prompt is empty."
        )

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:

        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured."
        )

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt
        )

        operation_name = getattr(
            operation,
            "name",
            None
        )

        if not operation_name:

            raise RuntimeError(
                "Video operation name missing."
            )

        return {
            "ok": True,
            "operation_id":
                str(operation_name)
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Video generation failed: "
                +
                str(exc)
        )


@app.get(
    "/api/autonomous/video/status/{operation_id:path}"
)
async def autonomous_video_status(
    operation_id: str
):

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:

        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured."
        )

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        operation = client.operations.get(
            name=operation_id
        )

        if not getattr(
            operation,
            "done",
            False
        ):

            return {
                "status":
                    "processing"
            }

        error = getattr(
            operation,
            "error",
            None
        )

        if error:

            return {
                "status":
                    "failed",
                "error":
                    str(error)
            }

        response = getattr(
            operation,
            "response",
            None
        )

        uri = None

        if response:

            videos = getattr(
                response,
                "generated_videos",
                None
            )

            if videos:

                video = getattr(
                    videos[0],
                    "video",
                    None
                )

                if video:

                    uri = getattr(
                        video,
                        "uri",
                        None
                    )

        result = {
            "status":
                "completed"
        }

        if uri:

            result["url"] = str(uri)

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Video status failed: "
                +
                str(exc)
        )


@app.post("/api/autonomous/transcribe")
async def autonomous_transcribe(
    file: UploadFile = File(...)
):

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:

        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured."
        )

    temporary = None

    try:

        suffix = (
            Path(
                file.filename
                or
                "voice.webm"
            ).suffix
            or
            ".webm"
        )

        temporary = (
            Path(
                tempfile.gettempdir()
            )
            /
            (
                "autonomous_voice_"
                +
                uuid.uuid4().hex
                +
                suffix
            )
        )

        temporary.write_bytes(
            await file.read()
        )

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        uploaded = client.files.upload(
            file=str(temporary)
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[
                "Transcribe this audio exactly.",
                uploaded,
            ]
        )

        return {
            "ok": True,
            "text":
                (
                    getattr(
                        response,
                        "text",
                        ""
                    )
                    or
                    ""
                ).strip()
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Transcription failed: "
                +
                str(exc)
        )

    finally:

        if temporary:

            try:
                temporary.unlink(
                    missing_ok=True
                )
            except Exception:
                pass


# === ACTUAL AUTONOMOUS ROUTES END ===

# FINAL_WEB_FEATURE_ROUTER
# === AUTONOMOUS CHESS COMPATIBILITY ROUTES ===

class AutonomousChessStartRequest(BaseModel):

    color: str = "white"
    difficulty: str = "Medium"


class AutonomousChessMoveRequest(BaseModel):

    game_id: str
    move: str


class AutonomousChessCloseRequest(BaseModel):

    game_id: str


@app.post("/api/autonomous/chess/start")
async def autonomous_chess_start(
    request: AutonomousChessStartRequest
):

    try:

        game = chess_start_game(
            request.color,
            request.difficulty
        )

        # Existing main.py already imports:
        # chess_start_game
        # chess.BLACK
        #
        # If the player selected Black, the AI must move first.

        try:

            if game.player_color == chess.BLACK:

                game.engine_move()

        except AttributeError:

            # Older chess service versions use a different
            # method name. Let the existing route/service
            # remain authoritative if so.
            pass

        return {
            "game_id":
                game.game_id,

            "fen":
                game.board.fen(),

            "color":
                (
                    "black"
                    if game.player_color == chess.BLACK
                    else "white"
                ),

            "difficulty":
                game.difficulty,

            "game_over":
                game.status()["game_over"]
                if hasattr(game, "status")
                else False,

            "result":
                game.status()["result"]
                if hasattr(game, "status")
                else None
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Chess start failed: "
                +
                str(exc)
        )


@app.post("/api/autonomous/chess/move")
async def autonomous_chess_move(
    request: AutonomousChessMoveRequest
):

    try:

        result = chess_make_player_move(
            request.game_id,
            request.move
        )

        return result

    except KeyError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Chess move failed: "
                +
                str(exc)
        )


@app.post("/api/autonomous/chess/close")
async def autonomous_chess_close(
    request: AutonomousChessCloseRequest
):

    try:

        chess_remove_game(
            request.game_id
        )

    except Exception:
        pass

    return {
        "ok": True
    }


@app.get("/api/autonomous/chess/test")
async def autonomous_chess_test():

    try:

        game = chess_start_game(
            "white",
            "Easy"
        )

        try:

            result = chess_make_player_move(
                game.game_id,
                "e2e4"
            )

            return {
                "ok": True,

                "ai_move":
                    result.get(
                        "engine_move"
                    ),

                "fen":
                    result.get(
                        "fen"
                    )
            }

        finally:

            try:

                chess_remove_game(
                    game.game_id
                )

            except Exception:
                pass

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Chess diagnostic failed: "
                +
                str(exc)
        )



# ============================================================
# V2 COMPATIBILITY / HISTORY / FILE READING ROUTES
# ============================================================

@app.get("/api/v2/chess/history")
async def v2_chess_history():
    try:
        return {"games": list_history()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chess history failed: {exc}")


@app.get("/api/v2/chess/analyze/{game_id}")
async def v2_chess_analyze(game_id: str):
    try:
        result = analyze_history(game_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chess analysis failed: {exc}")
    if not result:
        raise HTTPException(status_code=404, detail="Chess game not found.")
    return result


@app.get("/api/v2/chess/pgn/{game_id}")
async def v2_chess_pgn(game_id: str):
    game = get_history(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Chess game not found.")
    board = chess.Board()
    sans = []
    for item in game.get("moves", []):
        try:
            move = chess.Move.from_uci(item["uci"])
            if move in board.legal_moves:
                sans.append(board.san(move))
                board.push(move)
        except Exception:
            continue
    lines=[]
    for i in range(0, len(sans), 2):
        move_no=i//2+1
        line=f"{move_no}. {sans[i]}"
        if i+1 < len(sans): line += f" {sans[i+1]}"
        lines.append(line)
    result=game.get("result") or "*"
    pgn=(f'[Event "Autonomous AI"]\n[Date "{game.get("started_at", "")[:10]}"]\n'
         f'[White "Player" ]\n[Black "Autonomous AI"]\n[Result "{result}"]\n\n'
         + " ".join(lines) + f" {result}\n")
    return Response(content=pgn, media_type="application/x-chess-pgn", headers={"Content-Disposition": f'attachment; filename="chess_{game_id}.pgn"'})


@app.post("/api/v2/upload")
async def v2_upload_file(request: Request, file: UploadFile = File(...)):
    require_user(request)
    filename = Path(file.filename or "upload.bin").name
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB.")
    destination = UPLOAD_DIR / filename
    if destination.exists():
        stem, suffix = destination.stem, destination.suffix
        n=1
        while destination.exists():
            destination=UPLOAD_DIR / f"{stem}_{n}{suffix}"; n+=1
    destination.write_bytes(data)
    text=""
    ext=destination.suffix.lower()
    try:
        if ext in {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html", ".css", ".xml", ".yaml", ".yml", ".log", ".sql"}:
            text=data.decode("utf-8", errors="replace")
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader=PdfReader(str(destination))
            text="\n\n".join((page.extract_text() or "") for page in reader.pages)
        elif ext == ".docx":
            from docx import Document
            doc=Document(str(destination))
            text="\n".join(par.text for par in doc.paragraphs)
    except Exception as exc:
        text=f"[Could not extract text: {exc}]"
    text=text.strip()
    return {"ok":True,"filename":destination.name,"text":text[:60000],"text_preview":text[:2500],"size":len(data)}


@app.post("/api/v2/image")
async def v2_image(body: AutonomousImageRequest):
    try:
        return await autonomous_image(body)
    except HTTPException as exc:
        if exc.status_code == 500 and "429" in str(exc.detail):
            raise HTTPException(status_code=429, detail="Image generation quota is exhausted for the configured Gemini project. Add/enable Gemini API billing or use a project with image-generation quota, then try again.")
        raise


@app.post("/api/v2/video")
async def v2_video(body: AutonomousVideoRequest):
    try:
        return await autonomous_video(body)
    except HTTPException as exc:
        if exc.status_code == 500 and "429" in str(exc.detail):
            raise HTTPException(status_code=429, detail="Video generation quota is exhausted for the configured Gemini project. Check Gemini/Veo API quota and billing, then try again.")
        raise


@app.get("/api/v2/video/status/{operation_id:path}")
async def v2_video_status(operation_id: str):
    return await autonomous_video_status(operation_id)

# === AUTONOMOUS CHESS COMPATIBILITY ROUTES END ===

@app.get("/api/autonomous/chess/legal-moves")
async def autonomous_chess_legal_moves(
    game_id: str,
    square: str,
):

    import chess

    square = (square or "").strip().lower()
    if len(square) != 2 or square[0] not in "abcdefgh" or square[1] not in "12345678":
        raise HTTPException(status_code=400, detail="Invalid chess square.")

    try:
        game = chess_get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Chess game not found.")

    origin = chess.parse_square(square)
    piece = game.board.piece_at(origin)

    if piece is None or piece.color != game.player_color:
        return {"game_id": game_id, "square": square, "legal_moves": []}

    legal_moves = sorted({
        chess.square_name(move.to_square)
        for move in game.board.legal_moves
        if move.from_square == origin
    })

    return {
        "game_id": game_id,
        "square": square,
        "legal_moves": legal_moves,
    }

# ============================================================
# ============================================================

# ============================================================
# ADA CLOUD MEDIA ENGINE
# ============================================================

try:
    from cloud_media_router import router as cloud_media_router
    app.include_router(cloud_media_router)
except Exception as _cloud_media_error:
    print("[CLOUD MEDIA] Router unavailable:", _cloud_media_error)


# ADA CHESS ENGINE
try:
    from chess_router import router as ada_chess_router
    app.include_router(ada_chess_router)
except Exception as e:
    print("[CHESS]", e)



# ============================================================
# ADA CLOUD MEDIA
# ============================================================

try:
    from ada_media_router import router as ada_media_router
    app.include_router(ada_media_router)
    print("[MEDIA] Router enabled.")
except Exception as _media_error:
    print("[MEDIA] Optional router error:", _media_error)


# ============================================================
# GENERATED MEDIA STATIC FILES
# ============================================================

try:
    from fastapi.staticfiles import StaticFiles

    _ada_generated_images = (
        ROOT / "data" / "generated" / "images"
    )

    _ada_generated_videos = (
        ROOT / "data" / "generated" / "videos"
    )

    _ada_generated_images.mkdir(
        parents=True,
        exist_ok=True
    )

    _ada_generated_videos.mkdir(
        parents=True,
        exist_ok=True
    )

    app.mount(
        "/generated/images",
        StaticFiles(
            directory=str(_ada_generated_images)
        ),
        name="generated_images"
    )

    app.mount(
        "/generated/videos",
        StaticFiles(
            directory=str(_ada_generated_videos)
        ),
        name="generated_videos"
    )

except Exception as _generated_error:
    print(
        "[MEDIA STATIC] Optional:",
        _generated_error
    )











# ============================================================
# ADA FINAL CHESS FEATURE API
# ============================================================

@app.get("/api/autonomous/chess/state")
async def ada_chess_state(game_id: str):
    """
    Return authoritative chess state from python-chess.

    The frontend must NEVER guess whether the king is in check
    from the FEN string alone.
    """

    game = chess_get_game(game_id)

    if not game:
        return {
            "ok": False,
            "error": "Chess game not found"
        }

    board = game.board

    check = bool(board.is_check())

    check_square = None

    if check:
        try:
            king_square = board.king(board.turn)

            if king_square is not None:
                check_square = chess.square_name(king_square)

        except Exception:
            check_square = None

    legal_moves = []

    try:
        legal_moves = [
            move.uci()
            for move in board.legal_moves
        ]
    except Exception:
        legal_moves = []

    return {
        "ok": True,
        "game_id": game_id,
        "fen": board.fen(),
        "turn": "white" if board.turn else "black",
        "check": check,
        "check_square": check_square,
        "game_over": bool(board.is_game_over()),
        "result": game.result,
        "legal_moves": legal_moves,
        "moves": list(game.moves),
        "color": game.player_color,
        "difficulty": game.difficulty
    }


@app.post("/api/autonomous/chess/restart")
async def ada_chess_restart(payload: dict):
    color = str(payload.get("color", "white")).lower()
    difficulty = str(payload.get("difficulty", "Medium"))

    if color not in ("white", "black"):
        color = "white"

    if difficulty not in LEVELS:
        difficulty = "Medium"

    try:
        new_game = chess_start_game(
            color=color,
            difficulty=difficulty
        )

        # If the human selected black, the computer gets
        # the first move.
        if color == "black" and not new_game.board.is_game_over():
            new_game.engine_move()

        return {
            "ok": True,
            "game_id": new_game.game_id,
            "fen": new_game.board.fen(),
            "color": new_game.player_color,
            "difficulty": new_game.difficulty,
            "game_over": bool(new_game.board.is_game_over()),
            "result": new_game.result
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)
        }


@app.post("/api/autonomous/chess/resign")
async def ada_chess_resign(payload: dict):
    game_id = str(payload.get("game_id", ""))

    game = chess_get_game(game_id)

    if not game:
        return {
            "ok": False,
            "error": "Chess game not found"
        }

    if game.result:
        return {
            "ok": True,
            "fen": game.board.fen(),
            "result": game.result,
            "game_over": True
        }

    if str(game.player_color).lower() == "white":
        game.result = "0-1"
    else:
        game.result = "1-0"

    try:
        game._save()
    except Exception:
        pass

    return {
        "ok": True,
        "fen": game.board.fen(),
        "result": game.result,
        "game_over": True
    }


@app.post("/api/autonomous/chess/draw")
async def ada_chess_draw(payload: dict):
    game_id = str(payload.get("game_id", ""))

    game = chess_get_game(game_id)

    if not game:
        return {
            "ok": False,
            "error": "Chess game not found"
        }

    if game.result:
        return {
            "ok": True,
            "fen": game.board.fen(),
            "result": game.result,
            "game_over": True
        }

    game.result = "1/2-1/2"

    try:
        game._save()
    except Exception:
        pass

    return {
        "ok": True,
        "fen": game.board.fen(),
        "result": game.result,
        "game_over": True
    }


@app.post("/api/autonomous/chess/settings")
async def ada_chess_settings(payload: dict):
    game_id = str(payload.get("game_id", ""))
    difficulty = str(payload.get("difficulty", "Medium"))

    game = chess_get_game(game_id)

    if not game:
        return {
            "ok": False,
            "error": "Chess game not found"
        }

    if difficulty not in LEVELS:
        return {
            "ok": False,
            "error": "Invalid difficulty"
        }

    game.difficulty = difficulty

    try:
        game._save()
    except Exception:
        pass

    return {
        "ok": True,
        "game_id": game.game_id,
        "difficulty": game.difficulty,
        "fen": game.board.fen(),
        "game_over": bool(game.board.is_game_over()),
        "result": game.result
    }


# ============================================================
# LOCAL GEMINI VIDEO DOWNLOAD STATUS
# ============================================================

@app.get("/api/autonomous/video/local-status/{operation_id:path}")
async def ada_local_video_status(operation_id: str):

    try:

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return {
                "status": "error",
                "error": "GEMINI_API_KEY is not configured."
            }

        client = genai.Client(api_key=api_key)

        operation = client.operations.get(
            name=operation_id
        )

        if not getattr(operation, "done", False):

            return {
                "status": "processing",
                "operation_id": operation_id
            }

        # Gemini can report an operation as done while the
        # response itself contains an error.
        op_error = getattr(operation, "error", None)

        if op_error:
            return {
                "status": "error",
                "error": str(op_error)
            }

        response = getattr(operation, "response", None)

        if response is None:
            return {
                "status": "error",
                "error": "Gemini returned no video response."
            }

        videos = getattr(
            response,
            "generated_videos",
            None
        )

        if not videos:
            return {
                "status": "error",
                "error": "Gemini completed without a generated video."
            }

        generated = videos[0]

        video = getattr(
            generated,
            "video",
            None
        )

        if video is None:
            return {
                "status": "error",
                "error": "Gemini response did not contain a video file."
            }

        # Stable local filename.
        import hashlib

        safe_id = hashlib.sha256(
            operation_id.encode("utf-8")
        ).hexdigest()[:24]

        AUTONOMOUS_GENERATED_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = (
            AUTONOMOUS_GENERATED_DIR /
            f"gemini_video_{safe_id}.mp4"
        )

        if not destination.exists():

            client.files.download(
                file=video,
                destination=str(destination)
            )

        return {
            "status": "completed",
            "operation_id": operation_id,
            "url": f"/static/generated/{destination.name}"
        }

    except Exception as exc:

        return {
            "status": "error",
            "error": str(exc)
        }



