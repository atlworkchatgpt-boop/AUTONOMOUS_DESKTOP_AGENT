import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )

from agent.owner_config import (
    OWNER_NAME,
    GROQ_MODEL
)

from agent.smart_groq_ai import SmartGroqAI


class AnimatedAIController:

    def __init__(
        self,
        root,
        add_message,
        set_status
    ):

        self.root = root
        self.add_message = add_message
        self.set_status = set_status

        self.ai = None

        self.busy = False

        self.typing_job = None

        try:

            self.ai = SmartGroqAI()

        except Exception as exc:

            self.ai_error = str(exc)

        else:

            self.ai_error = ""

    # ========================================================
    # STATUS
    # ========================================================

    def status(self, text):

        try:
            self.root.after(
                0,
                lambda: self.set_status(text)
            )
        except Exception:
            pass

    # ========================================================
    # ANIMATED RESPONSE
    # ========================================================

    def animated_message(
        self,
        text
    ):

        self.add_message(
            "AI",
            ""
        )

        # dashboard implementations may expose
        # add_animated_message for true streaming.
        # Otherwise safely fall back to normal output.

        try:

            self.root.after(
                0,
                lambda: self._type_text(
                    text
                )
            )

        except Exception:

            self.add_message(
                "AI",
                text
            )

    def _type_text(
        self,
        text
    ):

        # Find the newest AI bubble if dashboard
        # exposes the expected helper.
        if hasattr(
            self,
            "typing_label"
        ):
            pass

        # The dashboard can override this method.
        self.add_message(
            "AI",
            text
        )

    # ========================================================
    # SEND
    # ========================================================

    def send(
        self,
        message,
        history
    ):

        if self.busy:
            return

        self.busy = True

        self.status(
            "● WORKING…"
        )

        def worker():

            try:

                if self.ai is None:

                    raise RuntimeError(
                        self.ai_error
                        or
                        "Groq AI unavailable."
                    )

                def progress(text):

                    self.status(
                        "● " + text.upper()
                    )

                answer = self.ai.ask(
                    message,
                    history,
                    progress
                )

                self.root.after(
                    0,
                    lambda: self.animated_message(
                        answer
                    )
                )

            except Exception as exc:

                safe_error = (
                    "I couldn't complete that request.\n\n"
                    + str(exc)
                )

                self.root.after(
                    0,
                    lambda: self.add_message(
                        "SYSTEM",
                        safe_error
                    )
                )

            finally:

                self.busy = False

                self.status(
                    "● READY"
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()
