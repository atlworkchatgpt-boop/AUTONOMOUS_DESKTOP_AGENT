AI_BG = '#212121'
import os
import sys
import json
import re
import time
import wave
import queue
import threading
import subprocess
import shutil
import webbrowser
import tempfile
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

# ============================================================
# PROJECT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

# ============================================================
# OPTIONAL PACKAGES
# ============================================================

try:
    from groq import Groq
    GROQ_OK = True
    GROQ_ERROR = ""
except Exception as e:
    Groq = None
    GROQ_OK = False
    GROQ_ERROR = str(e)

try:
    import requests
    REQUESTS_OK = True
except Exception:
    requests = None
    REQUESTS_OK = False

try:
    import sounddevice as sd
    SOUND_OK = True
except Exception:
    sd = None
    SOUND_OK = False

try:
    from pypdf import PdfReader
    PDF_OK = True
except Exception:
    PdfReader = None
    PDF_OK = False

# ============================================================
# PATHS
# ============================================================

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

SECURITY_DIR = PROJECT_ROOT / "security"
SECURITY_DIR.mkdir(exist_ok=True)

PASSWORD_FILE = SECURITY_DIR / "password.json"

MEMORY_FILE = PROJECT_ROOT / "data" / "chat_context" / "gngai_memory.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# COLORS
# ============================================================

BG = "#212121"
SIDEBAR = "#171717"
CHAT_BG = "#212121"
INPUT_BG = "#2f2f2f"
TEXT = "#ececec"
MUTED = "#9b9b9b"
ACCENT = "#10a37f"
HOVER = "#2a2a2a"
USER_BG = "#303030"
AI_BG = "#212121"
SYSTEM_BG = "#191919"
ERROR = "#ff6b6b"
WARNING = "#f0c674"

# ============================================================
# SETTINGS
# ============================================================

MAX_HISTORY = 30
MAX_FILE_CHARS = 50000

SYSTEM_PROMPT = """
You are GNG AI, an intelligent desktop assistant.

You are running locally on Windows and use Groq as your language model.

IMPORTANT BEHAVIOR:

1. Be accurate.
2. Never pretend something is current when you do not have current information.
3. When current information is requested, use the web-search capability supplied
   by the application instead of guessing.
4. Clearly distinguish known facts from uncertainty.
5. Give concise but useful answers.
6. Do not use excessive Markdown decoration.
7. Do not surround ordinary sentences with unnecessary asterisks.
8. You may help the owner operate their computer through the application's
   explicitly authorized tools.
9. Never claim that an action happened unless the application actually performed it.
10. Before destructive or security-sensitive operations, request confirmation.
11. Never reveal API keys, passwords, authentication tokens, or internal secrets.
12. If a task cannot safely be completed, explain why and offer a safe alternative.

You are GNG AI, not Gemini.
"""

# ============================================================
# PASSWORD / OWNER SECURITY
# ============================================================

def load_passwords():

    startup = None
    action = None

    try:
        if PASSWORD_FILE.exists():

            data = json.loads(
                PASSWORD_FILE.read_text(
                    encoding="utf-8"
                )
            )

            startup = (
                data.get("startup_password")
                or data.get("start_password")
                or data.get("password_start")
            )

            action = (
                data.get("action_password")
                or data.get("owner_password")
                or data.get("password")
            )

    except Exception:
        pass

    # Environment variables are supported without printing them.
    startup = startup or os.environ.get("GNG_AI_START_PASSWORD")
    action = action or os.environ.get("GNG_AI_ACTION_PASSWORD")

    return startup, action


START_PASSWORD, ACTION_PASSWORD = load_passwords()


def save_passwords(startup, action):

    SECURITY_DIR.mkdir(exist_ok=True)

    data = {
        "startup_password": startup,
        "action_password": action
    }

    PASSWORD_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


# ============================================================
# STARTUP SECURITY WINDOW
# ============================================================

class SecurityWindow:

    def __init__(self):

        self.result = False

        self.root = tk.Tk()

        self.root.title("GNG AI — Secure Access")

        self.root.geometry("520x360")

        self.root.resizable(False, False)

        self.root.configure(
            bg=BG
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.cancel
        )

        self.build()

        self.root.mainloop()


    def build(self):

        tk.Label(
            self.root,
            text="◉",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 38, "bold")
        ).pack(
            pady=(28, 0)
        )

        tk.Label(
            self.root,
            text="GNG AI",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 23, "bold")
        ).pack()

        tk.Label(
            self.root,
            text="SECURE OWNER ACCESS",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(
            pady=(2, 20)
        )

        box = tk.Frame(
            self.root,
            bg=INPUT_BG
        )

        box.pack(
            padx=60,
            fill="x"
        )

        self.entry = tk.Entry(
            box,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            show="●",
            font=("Segoe UI", 13)
        )

        self.entry.pack(
            padx=15,
            pady=14,
            fill="x"
        )

        self.entry.bind(
            "<Return>",
            lambda e: self.login()
        )

        tk.Button(
            self.root,
            text="UNLOCK GNG AI",
            command=self.login,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=25,
            pady=10
        ).pack(
            pady=20
        )

        tk.Label(
            self.root,
            text="Owner authentication required",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack()


    def login(self):

        global START_PASSWORD

        value = self.entry.get()

        if START_PASSWORD is None:

            # First-run setup.
            if not value:
                return

            START_PASSWORD = value

            if ACTION_PASSWORD is None:
                save_passwords(
                    START_PASSWORD,
                    START_PASSWORD
                )

            self.result = True
            self.root.destroy()
            return

        if value == START_PASSWORD:

            self.result = True
            self.root.destroy()

        else:

            self.entry.delete(
                0,
                "end"
            )

            messagebox.showerror(
                "Access denied",
                "Incorrect owner password."
            )


    def cancel(self):

        self.result = False

        self.root.destroy()


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "GNG AI — Autonomous Desktop Agent"
        )

        self.root.geometry(
            "1320x850"
        )

        self.root.minsize(
            980,
            680
        )

        self.root.configure(
            bg=BG
        )

        self.busy = False

        self.messages = []

        self.conversation = []

        self.client = None

        self.model = None

        self.selected_files = []

        self.web_enabled = True

        self.build_ui()

        self.load_memory()

        self.root.after(
            200,
            self.start_backend
        )


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        main = tk.Frame(
            self.root,
            bg=BG
        )

        main.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------

        sidebar = tk.Frame(
            main,
            bg=SIDEBAR,
            width=255
        )

        sidebar.pack(
            side="left",
            fill="y"
        )

        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="◉  GNG AI",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI", 17, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(22, 4)
        )

        tk.Label(
            sidebar,
            text="AUTONOMOUS DESKTOP AGENT",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 7)
        ).pack(
            anchor="w",
            padx=21,
            pady=(0, 20)
        )

        self.sidebar_button(
            sidebar,
            "＋  New chat",
            self.new_chat
        )

        self.sidebar_button(
            sidebar,
            "♟  Chess",
            self.open_chess
        )

        self.sidebar_button(
            sidebar,
            "📁  Upload files",
            self.upload
        )

        self.sidebar_button(
            sidebar,
            "🌐  Web search",
            self.search_web_button
        )

        self.sidebar_button(
            sidebar,
            "🎙  Voice",
            self.record_audio
        )

        self.sidebar_button(
            sidebar,
            "🖥  Computer actions",
            self.show_computer_help
        )

        self.sidebar_button(
            sidebar,
            "📋  Copy conversation",
            self.copy_chat
        )

        self.sidebar_button(
            sidebar,
            "🗑  Clear",
            self.clear_chat
        )

        tk.Frame(
            sidebar,
            bg=SIDEBAR
        ).pack(
            fill="both",
            expand=True
        )

        self.status = tk.Label(
            sidebar,
            text="● STARTING",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 9)
        )

        self.status.pack(
            anchor="w",
            padx=20
        )

        self.model_status = tk.Label(
            sidebar,
            text="Groq: checking...",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        )

        self.model_status.pack(
            anchor="w",
            padx=20,
            pady=(3, 0)
        )

        tk.Label(
            sidebar,
            text="Owner mode • Protected actions",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            padx=20,
            pady=(4, 20)
        )

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        content = tk.Frame(
            main,
            bg=CHAT_BG
        )

        content.pack(
            side="left",
            fill="both",
            expand=True
        )

        header = tk.Frame(
            content,
            bg=CHAT_BG,
            height=65
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="GNG AI",
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(
            side="left",
            padx=25
        )

        self.header_model = tk.Label(
            header,
            text="Connecting...",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        )

        self.header_model.pack(
            side="right",
            padx=25
        )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        chat_area = tk.Frame(
            content,
            bg=CHAT_BG
        )

        chat_area.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            chat_area,
            bg=CHAT_BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            chat_area,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.chat_frame = tk.Frame(
            self.canvas,
            bg=CHAT_BG
        )

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.chat_frame,
            anchor="nw"
        )

        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_chat
        )

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        input_area = tk.Frame(
            content,
            bg=CHAT_BG
        )

        input_area.pack(
            fill="x",
            padx=90,
            pady=(8, 6)
        )

        self.input = tk.Text(
            input_area,
            height=3,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            wrap="word",
            font=("Segoe UI", 11),
            padx=15,
            pady=12
        )

        self.input.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.input.bind(
            "<Return>",
            self.enter_handler
        )

        self.input.bind(
            "<Control-Return>",
            lambda e: self.send()
        )

        self.send_button = tk.Button(
            input_area,
            text="➤",
            command=self.send,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 15, "bold"),
            width=4,
            cursor="hand2"
        )

        self.send_button.pack(
            side="right",
            padx=(8, 0),
            fill="y"
        )

        bottom = tk.Frame(
            content,
            bg=CHAT_BG
        )

        bottom.pack(
            fill="x",
            padx=90
        )

        self.small_button(
            bottom,
            "📎",
            self.upload
        ).pack(
            side="left"
        )

        self.small_button(
            bottom,
            "🎙",
            self.record_audio
        ).pack(
            side="left"
        )

        self.small_button(
            bottom,
            "🌐",
            self.search_web_button
        ).pack(
            side="left"
        )

        tk.Label(
            bottom,
            text="Enter = send • Shift+Enter = new line",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            side="right"
        )

        tk.Label(
            content,
            text="GNG AI • Groq-powered • Web-aware • Protected computer control",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            pady=(5, 8)
        )

        self.add_message(
            "AI",
            "Welcome to GNG AI.\n\n"
            "Groq is the reasoning engine. I can chat, remember the current "
            "conversation, inspect uploaded text/PDF/code files, search the web "
            "for current information, record voice input, play chess, and perform "
            "approved Windows actions.\n\n"
            "Computer-control actions require owner authorization."
        )


    def sidebar_button(self, parent, text, command):

        button = tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            bg=SIDEBAR,
            fg=TEXT,
            activebackground=HOVER,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
            padx=18,
            pady=10,
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=8,
            pady=1
        )

        return button


    def small_button(self, parent, text, command):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=CHAT_BG,
            fg=MUTED,
            activebackground=HOVER,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 11),
            cursor="hand2"
        )


    def resize_chat(self, event):

        try:
            self.canvas.itemconfig(
                self.window_id,
                width=event.width
            )
        except Exception:
            pass


    # ========================================================
    # BACKEND
    # ========================================================

    def start_backend(self):

        if not GROQ_OK:

            self.set_error(
                "Groq SDK unavailable:\n\n" + GROQ_ERROR
            )

            return

        key = os.environ.get(
            "GROQ_API_KEY"
        )

        if not key:

            self.set_error(
                "GROQ_API_KEY was not found in this environment."
            )

            return

        threading.Thread(
            target=self.backend_worker,
            daemon=True
        ).start()


    def backend_worker(self):

        try:

            client = Groq(
                api_key=os.environ["GROQ_API_KEY"]
            )

            models = client.models.list()

            model_ids = []

            for item in models.data:

                model_id = getattr(
                    item,
                    "id",
                    ""
                )

                if model_id:
                    model_ids.append(
                        model_id
                    )

            # Prefer strong general chat models.
            preferences = [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant"
            ]

            selected = None

            for preferred in preferences:

                if preferred in model_ids:

                    selected = preferred
                    break

            if selected is None:

                chat_candidates = [
                    x for x in model_ids
                    if (
                        "llama" in x.lower()
                        or "qwen" in x.lower()
                        or "mixtral" in x.lower()
                    )
                    and "guard" not in x.lower()
                    and "whisper" not in x.lower()
                ]

                if chat_candidates:
                    selected = chat_candidates[0]

            if selected is None:
                raise RuntimeError(
                    "No suitable Groq chat model was returned."
                )

            self.client = client
            self.model = selected

            self.root.after(
                0,
                self.backend_ready
            )

        except Exception as e:

            self.root.after(
                0,
                lambda: self.set_error(
                    "Groq connection failed:\n\n" + str(e)
                )
            )


    def backend_ready(self):

        self.header_model.configure(
            text=self.model
        )

        self.model_status.configure(
            text="Groq: ONLINE",
            fg=ACCENT
        )

        self.status.configure(
            text="● READY",
            fg=ACCENT
        )

        self.add_message(
            "SYSTEM",
            "Groq connection established.\n"
            "Active model: " + str(self.model)
        )


    def set_error(self, text):

        self.header_model.configure(
            text="OFFLINE",
            fg=ERROR
        )

        self.model_status.configure(
            text="Groq: ERROR",
            fg=ERROR
        )

        self.status.configure(
            text="● ERROR",
            fg=ERROR
        )

        self.add_message(
            "SYSTEM",
            text
        )


    # ========================================================
    # MESSAGES
    # ========================================================

    def clean_answer(self, text):

        text = str(text)

        # Remove common Markdown decoration that was causing
        # the weird visible asterisks.
        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            text,
            flags=re.DOTALL
        )

        text = re.sub(
            r"(?<!\*)\*([^*\n]+)\*(?!\*)",
            r"\1",
            text
        )

        text = text.replace(
            "```",
            ""
        )

        return text.strip()


    def add_message(self, speaker, text):

        text = self.clean_answer(text)

        self.messages.append(
            {
                "speaker": speaker,
                "text": text
            }
        )

        outer = tk.Frame(
            self.chat_frame,
            bg=CHAT_BG
        )

        outer.pack(
            fill="x",
            padx=70,
            pady=10
        )

        if speaker == "YOU":

            name = "You"
            bubble_bg = USER_BG

        elif speaker == "SYSTEM":

            name = "System"
            bubble_bg = SYSTEM_BG

        else:

            name = "GNG AI"
            bubble_bg = AI_BG

        top = tk.Frame(
            outer,
            bg=CHAT_BG
        )

        top.pack(
            fill="x"
        )

        tk.Label(
            top,
            text=name,
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(
            side="left"
        )

        tk.Button(
            top,
            text="Copy",
            command=lambda x=text: self.copy_text(x),
            bg=CHAT_BG,
            fg=MUTED,
            activebackground=HOVER,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 8),
            cursor="hand2"
        ).pack(
            side="right"
        )

        bubble = tk.Frame(
            outer,
            bg=bubble_bg
        )

        bubble.pack(
            fill="x",
            pady=(4, 0)
        )

        tk.Label(
            bubble,
            text=text,
            bg=bubble_bg,
            fg=TEXT,
            justify="left",
            anchor="w",
            wraplength=900,
            font=("Segoe UI", 11),
            padx=15,
            pady=13
        ).pack(
            fill="x"
        )

        self.root.after(
            50,
            lambda: self.canvas.yview_moveto(1)
        )


    # ========================================================
    # CHAT
    # ========================================================

    def enter_handler(self, event):

        if event.state & 0x0001:
            return

        self.send()

        return "break"


    def send(self):

        if self.busy:
            return

        message = self.input.get(
            "1.0",
            "end"
        ).strip()

        if not message:
            return

        self.input.delete(
            "1.0",
            "end"
        )

        self.add_message(
            "YOU",
            message
        )

        # ----------------------------------------------------
        # COMPUTER ACTION ROUTER
        # ----------------------------------------------------

        action = self.detect_computer_action(
            message
        )

        if action:

            self.handle_computer_action(
                action
            )

            return

        # ----------------------------------------------------
        # NORMAL AI
        # ----------------------------------------------------

        if self.client is None:

            self.add_message(
                "SYSTEM",
                "Groq is still connecting. Please wait."
            )

            return

        self.conversation.append(
            {
                "role": "user",
                "content": message
            }
        )

        self.conversation = self.conversation[
            -MAX_HISTORY:
        ]

        self.busy = True

        self.send_button.configure(
            state="disabled",
            text="…"
        )

        self.status.configure(
            text="● THINKING",
            fg=WARNING
        )

        threading.Thread(
            target=self.ai_worker,
            daemon=True
        ).start()


    def ai_worker(self):

        try:

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]

            messages.extend(
                self.conversation[-MAX_HISTORY:]
            )

            # Add selected file context.
            file_context = self.get_file_context()

            if file_context:

                messages.append(
                    {
                        "role": "system",
                        "content":
                            "The following files were uploaded by the owner. "
                            "Use them when relevant:\n\n"
                            + file_context
                    }
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
                max_tokens=2500
            )

            answer = response.choices[0].message.content

            if not answer:
                answer = "The model returned an empty response."

            answer = self.clean_answer(
                answer
            )

        except Exception as e:

            answer = (
                "I couldn't complete the request.\n\n"
                "Groq error:\n"
                + str(e)
            )

        self.root.after(
            0,
            lambda: self.finish_answer(answer)
        )


    def finish_answer(self, answer):

        self.conversation.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        self.conversation = self.conversation[
            -MAX_HISTORY:
        ]

        self.add_message(
            "AI",
            answer
        )

        self.save_memory()

        self.busy = False

        self.send_button.configure(
            state="normal",
            text="➤"
        )

        self.status.configure(
            text="● READY",
            fg=ACCENT
        )


    # ========================================================
    # MEMORY
    # ========================================================

    def load_memory(self):

        try:

            if MEMORY_FILE.exists():

                data = json.loads(
                    MEMORY_FILE.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(data, list):

                    self.conversation = data[
                        -MAX_HISTORY:
                    ]

        except Exception:
            self.conversation = []


    def save_memory(self):

        try:

            MEMORY_FILE.write_text(
                json.dumps(
                    self.conversation[-MAX_HISTORY:],
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

        except Exception:
            pass


    # ========================================================
    # FILES
    # ========================================================

    def upload(self):

        paths = filedialog.askopenfilenames(
            title="Upload files"
        )

        if not paths:
            return

        self.selected_files = []

        for source in paths:

            try:

                source = Path(source)

                destination = UPLOAD_DIR / source.name

                if destination.exists():

                    stamp = int(
                        time.time()
                    )

                    destination = (
                        UPLOAD_DIR
                        / f"{source.stem}_{stamp}{source.suffix}"
                    )

                shutil.copy2(
                    source,
                    destination
                )

                self.selected_files.append(
                    destination
                )

            except Exception as e:

                self.add_message(
                    "SYSTEM",
                    "File upload failed:\n" + str(e)
                )

        if self.selected_files:

            names = "\n".join(
                f"• {p.name}"
                for p in self.selected_files
            )

            self.add_message(
                "SYSTEM",
                "Files uploaded:\n\n" + names
            )


    def read_file(self, path):

        path = Path(path)

        try:

            suffix = path.suffix.lower()

            if suffix == ".pdf" and PDF_OK:

                reader = PdfReader(
                    str(path)
                )

                chunks = []

                for page in reader.pages:

                    try:
                        chunks.append(
                            page.extract_text() or ""
                        )
                    except Exception:
                        pass

                return "\n".join(chunks)[
                    :MAX_FILE_CHARS
                ]

            if suffix in {
                ".txt",
                ".md",
                ".py",
                ".json",
                ".csv",
                ".log",
                ".xml",
                ".html",
                ".css",
                ".js",
                ".ts",
                ".yaml",
                ".yml"
            }:

                return path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )[:MAX_FILE_CHARS]

        except Exception:
            pass

        return ""


    def get_file_context(self):

        if not self.selected_files:
            return ""

        chunks = []

        for path in self.selected_files:

            text = self.read_file(
                path
            )

            if text:

                chunks.append(
                    f"===== {path.name} =====\n{text}"
                )

        return "\n\n".join(
            chunks
        )[:MAX_FILE_CHARS]


    # ========================================================
    # WEB SEARCH
    # ========================================================

    def search_web_button(self):

        query = self.input.get(
            "1.0",
            "end"
        ).strip()

        if not query:

            self.input.focus_set()

            self.add_message(
                "SYSTEM",
                "Type your search question in the message box first."
            )

            return

        self.input.delete(
            "1.0",
            "end"
        )

        self.add_message(
            "YOU",
            query
        )

        self.web_search(
            query
        )


    def web_search(self, query):

        if not REQUESTS_OK:

            self.add_message(
                "SYSTEM",
                "The requests package is unavailable."
            )

            return

        self.busy = True

        self.status.configure(
            text="● SEARCHING WEB",
            fg=WARNING
        )

        threading.Thread(
            target=self.web_worker,
            args=(query,),
            daemon=True
        ).start()


    def web_worker(self, query):

        try:

            url = (
                "https://html.duckduckgo.com/html/"
            )

            response = requests.get(
                url,
                params={"q": query},
                headers={
                    "User-Agent":
                        "Mozilla/5.0"
                },
                timeout=12
            )

            response.raise_for_status()

            html = response.text

            results = []

            # Extract result titles/URLs from DDG HTML.
            pattern = re.compile(
                r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                re.I | re.S
            )

            for match in pattern.finditer(html):

                link = match.group(1)

                title = re.sub(
                    "<.*?>",
                    "",
                    match.group(2)
                )

                title = (
                    title
                    .replace("&amp;", "&")
                    .replace("&quot;", '"')
                )

                if link.startswith("//"):
                    link = "https:" + link

                results.append(
                    {
                        "title": title.strip(),
                        "url": link
                    }
                )

                if len(results) >= 6:
                    break

            if not results:

                raise RuntimeError(
                    "No search results were returned."
                )

            context = "\n".join(
                f"{i+1}. {r['title']}\n{r['url']}"
                for i, r in enumerate(results)
            )

            answer = self.summarize_web(
                query,
                context
            )

            self.root.after(
                0,
                lambda: self.finish_web(
                    answer,
                    results
                )
            )

        except Exception as e:

            self.root.after(
                0,
                lambda: self.finish_web_error(
                    str(e)
                )
            )


    def summarize_web(self, query, context):

        if self.client is None:

            return (
                "Search results found:\n\n"
                + context
            )

        prompt = (
            "Answer the user's question using these fresh web "
            "search results. Do not invent facts. If the results "
            "are insufficient, say so. Mention that information "
            "may change.\n\n"
            "QUESTION:\n"
            + query
            + "\n\nRESULTS:\n"
            + context
        )

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1800
            )

            return self.clean_answer(
                response.choices[0].message.content
            )

        except Exception:

            return (
                "Fresh search results:\n\n"
                + context
            )


    def finish_web(self, answer, results):

        self.add_message(
            "AI",
            answer
        )

        sources = "\n".join(
            f"• {r['title']}\n  {r['url']}"
            for r in results
        )

        self.add_message(
            "SYSTEM",
            "Web sources used:\n\n" + sources
        )

        self.busy = False

        self.status.configure(
            text="● READY",
            fg=ACCENT
        )


    def finish_web_error(self, error):

        self.add_message(
            "SYSTEM",
            "Web search failed:\n\n" + error
        )

        self.busy = False

        self.status.configure(
            text="● READY",
            fg=ACCENT
        )


    # ========================================================
    # COMPUTER CONTROL
    # ========================================================

    def detect_computer_action(self, message):

        text = message.lower().strip()

        # Safe application launching.
        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe"
        }

        for name, command in apps.items():

            if (
                text == f"open {name}"
                or text == f"launch {name}"
                or text == f"start {name}"
            ):

                return {
                    "type": "open_app",
                    "name": name,
                    "command": command
                }

        if text in {
            "open vscode",
            "launch vscode",
            "start vscode"
        }:

            return {
                "type": "open_vscode"
            }

        return None


    def handle_computer_action(self, action):

        if ACTION_PASSWORD is None:

            self.add_message(
                "SYSTEM",
                "Computer-control password has not been configured."
            )

            return

        self.request_action_password(
            action
        )


    def request_action_password(self, action):

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "GNG AI — Action Authorization"
        )

        dialog.geometry(
            "480x300"
        )

        dialog.resizable(
            False,
            False
        )

        dialog.configure(
            bg=BG
        )

        tk.Label(
            dialog,
            text="🔐  AUTHORIZATION REQUIRED",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(
            pady=(28, 12)
        )

        if action["type"] == "open_app":

            description = (
                "Open " + action["name"]
            )

        elif action["type"] == "open_vscode":

            description = "Open Visual Studio Code"

        else:

            description = "Perform computer action"

        tk.Label(
            dialog,
            text=description,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(
            pady=5
        )

        entry = tk.Entry(
            dialog,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            show="●",
            relief="flat",
            font=("Segoe UI", 12)
        )

        entry.pack(
            padx=60,
            fill="x",
            pady=18,
            ipady=8
        )

        entry.focus_set()

        def approve():

            if entry.get() != ACTION_PASSWORD:

                entry.delete(
                    0,
                    "end"
                )

                messagebox.showerror(
                    "Authorization denied",
                    "Incorrect action password.",
                    parent=dialog
                )

                return

            dialog.destroy()

            self.execute_action(
                action
            )

        tk.Button(
            dialog,
            text="AUTHORIZE",
            command=approve,
            bg=ACCENT,
            fg="white",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padx=25,
            pady=9
        ).pack()

        entry.bind(
            "<Return>",
            lambda e: approve()
        )


    def execute_action(self, action):

        try:

            if action["type"] == "open_app":

                subprocess.Popen(
                    action["command"],
                    shell=False
                )

                self.add_message(
                    "SYSTEM",
                    "Opened " + action["name"] + "."
                )

            elif action["type"] == "open_vscode":

                code = shutil.which(
                    "code"
                )

                if code:

                    subprocess.Popen(
                        [code]
                    )

                    self.add_message(
                        "SYSTEM",
                        "Visual Studio Code opened."
                    )

                else:

                    self.add_message(
                        "SYSTEM",
                        "The 'code' command was not found."
                    )

        except Exception as e:

            self.add_message(
                "SYSTEM",
                "Computer action failed:\n\n" + str(e)
            )


    def show_computer_help(self):

        self.add_message(
            "SYSTEM",
            "Protected computer actions currently include:\n\n"
            "• Open Notepad\n"
            "• Open Calculator\n"
            "• Open Paint\n"
            "• Open File Explorer\n"
            "• Open VS Code\n\n"
            "Each computer action requires the owner action password.\n\n"
            "I intentionally do not allow the language model to silently "
            "execute arbitrary destructive commands."
        )


    # ========================================================
    # VOICE
    # ========================================================

    def record_audio(self):

        if not SOUND_OK:

            self.add_message(
                "SYSTEM",
                "Voice requires the sounddevice package."
            )

            return

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "GNG AI — Voice"
        )

        dialog.geometry(
            "420x240"
        )

        dialog.configure(
            bg=BG
        )

        tk.Label(
            dialog,
            text="🎙  VOICE INPUT",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 17, "bold")
        ).pack(
            pady=(30, 8)
        )

        tk.Label(
            dialog,
            text="Record up to 10 seconds.",
            bg=BG,
            fg=MUTED
        ).pack()

        seconds = tk.IntVar(
            value=5
        )

        tk.Spinbox(
            dialog,
            from_=1,
            to=10,
            textvariable=seconds,
            width=5
        ).pack(
            pady=12
        )

        def start():

            duration = max(
                1,
                min(
                    10,
                    int(seconds.get())
                )
            )

            dialog.destroy()

            self.start_recording(
                duration
            )

        tk.Button(
            dialog,
            text="START RECORDING",
            command=start,
            bg=ACCENT,
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=9
        ).pack()


    def start_recording(self, duration):

        self.add_message(
            "SYSTEM",
            f"Recording for {duration} seconds..."
        )

        threading.Thread(
            target=self.record_worker,
            args=(duration,),
            daemon=True
        ).start()


    def record_worker(self, duration):

        try:

            samplerate = 16000

            recording = sd.rec(
                int(
                    duration
                    * samplerate
                ),
                samplerate=samplerate,
                channels=1,
                dtype="int16"
            )

            sd.wait()

            path = (
                UPLOAD_DIR
                / "gngai_voice.wav"
            )

            with wave.open(
                str(path),
                "wb"
            ) as wf:

                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(
                    recording.tobytes()
                )

            text = self.transcribe_audio(
                path
            )

            self.root.after(
                0,
                lambda: self.voice_finished(
                    text
                )
            )

        except Exception as e:

            self.root.after(
                0,
                lambda: self.add_message(
                    "SYSTEM",
                    "Voice recording failed:\n\n"
                    + str(e)
                )
            )


    def transcribe_audio(self, path):

        if self.client is None:

            return (
                "Groq is not connected yet."
            )

        try:

            with open(
                path,
                "rb"
            ) as audio:

                result = self.client.audio.transcriptions.create(
                    file=audio,
                    model="whisper-large-v3-turbo",
                    response_format="text"
                )

            return str(result).strip()

        except Exception as e:

            return (
                "Voice transcription failed:\n\n"
                + str(e)
            )


    def voice_finished(self, text):

        self.add_message(
            "SYSTEM",
            "Transcription:\n\n" + text
        )

        if text and not text.lower().startswith(
            "voice transcription failed"
        ):

            self.input.insert(
                "end",
                text
            )


    # ========================================================
    # CHESS
    # ========================================================

    def open_chess(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "GNG AI — Chess"
        )

        window.geometry(
            "720x760"
        )

        window.configure(
            bg=BG
        )

        tk.Label(
            window,
            text="♟  CHESS MODE",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(
            pady=(18, 3)
        )

        tk.Label(
            window,
            text="Interactive board",
            bg=BG,
            fg=MUTED
        ).pack(
            pady=(0, 12)
        )

        size = 560
        sq = size // 8

        canvas = tk.Canvas(
            window,
            width=size,
            height=size,
            highlightthickness=0
        )

        canvas.pack()

        pieces = [
            ["♜","♞","♝","♛","♚","♝","♞","♜"],
            ["♟","♟","♟","♟","♟","♟","♟","♟"],
            ["","","","","","","",""],
            ["","","","","","","",""],
            ["","","","","","","",""],
            ["","","","","","","",""],
            ["♙","♙","♙","♙","♙","♙","♙","♙"],
            ["♖","♘","♗","♕","♔","♗","♘","♖"]
        ]

        selected = [None]

        def draw():

            canvas.delete(
                "all"
            )

            for r in range(8):

                for c in range(8):

                    x1 = c * sq
                    y1 = r * sq
                    x2 = x1 + sq
                    y2 = y1 + sq

                    light = (
                        (r + c) % 2 == 0
                    )

                    canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=(
                            "#f0d9b5"
                            if light
                            else "#b58863"
                        ),
                        outline=""
                    )

                    piece = pieces[r][c]

                    if piece:

                        canvas.create_text(
                            x1 + sq / 2,
                            y1 + sq / 2,
                            text=piece,
                            font=("Segoe UI Symbol", 40),
                            fill="#111111"
                        )

            if selected[0]:

                r, c = selected[0]

                canvas.create_rectangle(
                    c * sq,
                    r * sq,
                    (c + 1) * sq,
                    (r + 1) * sq,
                    outline=ACCENT,
                    width=5
                )


        def click(event):

            c = event.x // sq
            r = event.y // sq

            if not (
                0 <= r < 8
                and
                0 <= c < 8
            ):
                return

            if selected[0] is None:

                if pieces[r][c]:

                    selected[0] = (
                        r,
                        c
                    )

            else:

                sr, sc = selected[0]

                pieces[r][c] = pieces[sr][sc]

                pieces[sr][sc] = ""

                selected[0] = None

            draw()


        canvas.bind(
            "<Button-1>",
            click
        )

        draw()

        tk.Label(
            window,
            text="Board interaction enabled. Legal-move enforcement can be added as a separate chess engine layer.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            pady=12
        )


    # ========================================================
    # COPY / CLEAR
    # ========================================================

    def copy_text(self, text):

        self.root.clipboard_clear()

        self.root.clipboard_append(
            text
        )

        self.status.configure(
            text="● COPIED",
            fg=ACCENT
        )

        self.root.after(
            1200,
            lambda: self.status.configure(
                text="● READY",
                fg=ACCENT
            )
        )


    def copy_chat(self):

        text = "\n\n".join(
            f"{m['speaker']}:\n{m['text']}"
            for m in self.messages
        )

        if text:
            self.copy_text(
                text
            )


    def clear_chat(self):

        if not self.messages:
            return

        if not messagebox.askyesno(
            "Clear",
            "Clear this conversation?"
        ):
            return

        self.new_chat()


    def new_chat(self):

        for widget in self.chat_frame.winfo_children():

            widget.destroy()

        self.messages = []

        self.conversation = []

        self.save_memory()

        self.add_message(
            "AI",
            "New conversation started."
        )


# ============================================================
# LAUNCH
# ============================================================

def run_dashboard():

    security = SecurityWindow()

    if not security.result:
        return

    root = tk.Tk()

    Dashboard(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    run_dashboard()
