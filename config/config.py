from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

SCREENSHOT_DIR = DATA_DIR / "screenshots"
BACKUP_DIR = DATA_DIR / "backups"
CHAT_UPLOAD_DIR = DATA_DIR / "chat_uploads"
CHAT_CONTEXT_DIR = DATA_DIR / "chat_context"
VOICE_DIR = DATA_DIR / "voice"
WORKSPACE_DIR = DATA_DIR / "agent_workspace"

DB_PATH = DATA_DIR / "agent_memory.db"


for folder in (
    DATA_DIR,
    SCREENSHOT_DIR,
    BACKUP_DIR,
    CHAT_UPLOAD_DIR,
    CHAT_CONTEXT_DIR,
    VOICE_DIR,
    WORKSPACE_DIR,
):
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )


OWNER_NAME = "Shreyansh Ray"


# ============================================================
# PASSWORDS
# ============================================================

START_PASSWORD = "gngaistart"
ACTION_PASSWORD = "gngai"

MAX_PASSWORD_ATTEMPTS = 3

# gngai must be entered for each protected action.
ACTION_AUTH_SESSION_SECONDS = 0

# Compatibility name.
AUTH_SESSION_SECONDS = 0


# ============================================================
# AI
# ============================================================

AI_MODEL = "qwen2.5:1.5b"

OLLAMA_URL = (
    "http://127.0.0.1:11434/api/chat"
)

AI_TIMEOUT = 90

MAX_CONTEXT_MESSAGES = 2
MAX_AI_OUTPUT = 160

AI_CONTEXT_MESSAGES = MAX_CONTEXT_MESSAGES
AI_MAX_OUTPUT = MAX_AI_OUTPUT


# ============================================================
# SAFETY
# ============================================================

PROTECTED_ACTIONS = {
    "delete",
    "install",
    "close",
}


DANGEROUS_COMMAND_WORDS = {
    "del",
    "erase",
    "rmdir",
    "rd",
    "format",
    "shutdown",
    "restart",
    "diskpart",
    "taskkill",
    "remove-item",
    "rm",
    "sudo",
}


PERSONAL_INFO_KEYWORDS = {
    "my password",
    "my email",
    "my address",
    "my phone",
    "my telephone",
    "my personal",
    "my private",
    "my account",
    "my login",
    "my username",
    "my credentials",
    "personal information",
    "private information",
    "personal data",
}