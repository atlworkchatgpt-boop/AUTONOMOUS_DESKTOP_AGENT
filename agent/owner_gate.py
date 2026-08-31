import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PASSWORD_FILE = (
    ROOT /
    "security" /
    "password.json"
)


def owner_exists():

    return PASSWORD_FILE.exists()


def owner_label():

    return "OWNER"


def requires_confirmation(command):

    text = str(command).lower()

    dangerous_words = [
        "delete",
        "remove",
        "uninstall",
        "format",
        "wipe",
        "erase",
        "shutdown",
        "restart",
        "registry",
        "overwrite",
        "replace",
        "kill process"
    ]

    return any(
        word in text
        for word in dangerous_words
    )


def action_allowed(command, confirmed=False):

    if requires_confirmation(command):
        return bool(confirmed)

    return True
