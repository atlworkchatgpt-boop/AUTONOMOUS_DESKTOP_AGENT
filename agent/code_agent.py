from datetime import datetime
from pathlib import Path
import shutil

from config.config import (
    BACKUP_DIR,
    MAX_FILE_READ,
)


class CodeAgent:

    def __init__(
        self,
        authentication,
        logger,
    ):

        self.authentication = authentication
        self.logger = logger

    def scan_project(
        self,
        project_path,
    ):

        root = Path(
            project_path
        ).expanduser().resolve()

        if not root.exists():

            return {
                "ok": False,
                "error": f"Project not found: {root}",
            }

        if not root.is_dir():

            return {
                "ok": False,
                "error": f"Not a directory: {root}",
            }

        ignored = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".idea",
            ".vs",
            "dist",
            "build",
        }

        files = []

        for path in root.rglob("*"):

            try:

                relative = path.relative_to(
                    root
                )

            except Exception:

                continue

            if any(
                part in ignored
                for part in relative.parts
            ):
                continue

            if path.is_file():

                files.append(
                    str(relative)
                )

        files.sort()

        return {
            "ok": True,
            "project": str(root),
            "files": files[:1000],
        }

    def read_code(
        self,
        path,
    ):

        p = Path(
            path
        ).expanduser().resolve()

        if not p.is_file():

            return {
                "ok": False,
                "error": f"File not found: {p}",
            }

        try:

            return {
                "ok": True,
                "path": str(p),
                "content": p.read_text(
                    encoding="utf-8",
                    errors="replace",
                )[:MAX_FILE_READ],
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc),
            }

    def write_code(
        self,
        path,
        content,
    ):

        if not self.authentication.require_action_auth(
            (
                "Code modification requested.\n\n"
                f"File:\n{path}"
            )
        ):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Code modification cancelled.",
            }

        p = Path(
            path
        ).expanduser().resolve()

        try:

            if p.exists():

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                backup_name = (
                    f"{p.stem}_{timestamp}"
                    f"{p.suffix}.bak"
                )

                backup_path = (
                    BACKUP_DIR
                    / backup_name
                )

                shutil.copy2(
                    p,
                    backup_path,
                )

            p.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            p.write_text(
                content,
                encoding="utf-8",
            )

            return {
                "ok": True,
                "path": str(p),
                "message": (
                    f"Code written successfully: {p}"
                ),
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc),
            }