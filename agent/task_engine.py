import re
import time

from .desktop_executor import desktop


class TaskEngine:

    def __init__(self, status_callback=None):
        self.status = status_callback or (lambda x: None)

    def run(self, request):

        text = request.strip()
        lower = text.lower()

        # ----------------------------------------------------
        # OPEN APPLICATION
        # ----------------------------------------------------

        app = None

        patterns = [
            r"\bopen\s+(notepad)\b",
            r"\bopen\s+(calculator|calc)\b",
            r"\bopen\s+(paint)\b",
            r"\bopen\s+(chrome)\b",
            r"\bopen\s+(edge)\b",
            r"\bopen\s+(vscode|vs code)\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                lower
            )

            if match:
                app = match.group(1)
                break

        if app:

            normalized = {
                "calculator": "calculator",
                "calc": "calculator",
                "vscode": "vscode",
                "vs code": "vscode"
            }.get(app, app)

            self.status(
                f"Opening {normalized}..."
            )

            result = desktop.open_application(
                normalized
            )

            if not result["success"]:
                return result

            self.status(
                f"{normalized.title()} opened."
            )

            # ------------------------------------------------
            # TYPE REQUEST
            # ------------------------------------------------

            type_match = re.search(
                r"(?:type|write|enter)\s+(?:this\s+)?(.+)",
                text,
                flags=re.I | re.S
            )

            if type_match:

                content = type_match.group(1).strip()

                if content:

                    self.status(
                        "Typing..."
                    )

                    time.sleep(1)

                    result = desktop.type_text(
                        content
                    )

                    if not result["success"]:
                        return result

                    self.status(
                        "Typing completed."
                    )

                    return {
                        "success": True,
                        "message":
                            f"{normalized.title()} opened and "
                            "the requested text was typed."
                    }

            return {
                "success": True,
                "message":
                    f"{normalized.title()} opened successfully."
            }

        return {
            "success": False,
            "handled": False
        }


task_engine = TaskEngine()
