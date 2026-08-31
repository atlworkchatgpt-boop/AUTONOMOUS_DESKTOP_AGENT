import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.chdir(ROOT)


# ============================================================
# EXISTING PROJECT COMPONENTS
# ============================================================

try:
    from agent.tools_registry import ToolRegistry
except Exception:
    ToolRegistry = None

try:
    from agent.real_groq_agent import RealGroqAgent
except Exception:
    RealGroqAgent = None


# ============================================================
# CONFIG
# ============================================================

START_PASSWORD = "gngaistart"
ACTION_PASSWORD = "gngai"

UPLOAD_DIR = os.path.join(
    ROOT,
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# UI
# ============================================================

BG = "#212121"
SIDEBAR = "#171717"
INPUT_BG = "#303030"
CARD = "#2A2A2A"
TEXT = "#EEEEEE"
MUTED = "#999999"
ACCENT = "#10A37F"
DANGER = "#A93C3C"
USER_BG = "#303030"


# ============================================================
# APPLICATION
# ============================================================

class AutonomousDesktopAI:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(
            "Autonomous Desktop AI"
        )

        self.root.geometry(
            "1280x820"
        )

        self.root.minsize(
            950,
            650
        )

        self.root.configure(
            bg=BG
        )

        self.running = False
        self.stop_event = threading.Event()

        self.messages = []
        self.conversation = []

        self.chat_widgets = []

        self.authenticated = False

        self.show_startup_screen()

    # ========================================================
    # STARTUP SCREEN
    # ========================================================

    def show_startup_screen(self):

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(
            bg="#181818"
        )

        outer = tk.Frame(
            self.root,
            bg="#181818"
        )

        outer.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        tk.Label(
            outer,
            text="🔐",
            bg="#181818",
            fg=TEXT,
            font=("Segoe UI Emoji", 38)
        ).pack(
            pady=(0, 8)
        )

        tk.Label(
            outer,
            text="AUTONOMOUS DESKTOP AI",
            bg="#181818",
            fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack()

        tk.Label(
            outer,
            text="Secure startup",
            bg="#181818",
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(
            pady=(5, 25)
        )

        self.password_entry = tk.Entry(
            outer,
            show="●",
            width=30,
            bg="#2B2B2B",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            justify="center",
            font=("Segoe UI", 13)
        )

        self.password_entry.pack(
            ipady=12
        )

        self.password_entry.focus_force()

        self.password_status = tk.Label(
            outer,
            text="Enter startup password",
            bg="#181818",
            fg=MUTED,
            font=("Segoe UI", 9)
        )

        self.password_status.pack(
            pady=10
        )

        row = tk.Frame(
            outer,
            bg="#181818"
        )

        row.pack(
            fill="x",
            pady=8
        )

        tk.Button(
            row,
            text="EXIT",
            command=self.root.destroy,
            bg="#3A3A3A",
            fg=TEXT,
            activebackground="#4A4A4A",
            relief="flat",
            bd=0,
            padx=28,
            pady=11,
            cursor="hand2"
        ).pack(
            side="left"
        )

        tk.Button(
            row,
            text="UNLOCK",
            command=self.unlock,
            bg=ACCENT,
            fg="white",
            activebackground="#0D8E6F",
            relief="flat",
            bd=0,
            padx=28,
            pady=11,
            cursor="hand2"
        ).pack(
            side="right"
        )

        self.root.bind(
            "<Return>",
            lambda event: self.unlock()
        )

    def unlock(self):

        if self.password_entry.get() != START_PASSWORD:

            self.password_entry.delete(
                0,
                "end"
            )

            self.password_status.configure(
                text="Incorrect password",
                fg="#FF6B6B"
            )

            return

        self.authenticated = True

        self.build_dashboard()

    # ========================================================
    # DASHBOARD
    # ========================================================

    def build_dashboard(self):

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(
            bg=BG
        )

        self.build_sidebar()
        self.build_main_area()

        self.add_message(
            "AI",
            (
                "Welcome. 👋\n\n"
                "Autonomous Desktop AI is ready.\n\n"
                "Connected capabilities can include:\n"
                "• Groq AI\n"
                "• Desktop tools\n"
                "• Web tools\n"
                "• File upload\n"
                "• Copy controls\n"
                "• Stockfish chess\n\n"
                "Type a request and press SEND."
            )
        )

    # ========================================================
    # SIDEBAR
    # ========================================================

    def build_sidebar(self):

        self.sidebar = tk.Frame(
            self.root,
            bg=SIDEBAR,
            width=250
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(
            False
        )

        tk.Label(
            self.sidebar,
            text="◉  AUTONOMOUS AI",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(24, 22)
        )

        self.side_button(
            "＋  New Chat",
            self.new_chat
        )

        self.side_button(
            "♟  Chess • Stockfish",
            self.open_chess
        )

        self.side_button(
            "📁  Upload",
            self.upload
        )

        self.side_button(
            "📋  Copy Conversation",
            self.copy_conversation
        )

        self.side_button(
            "🗑  Clear Conversation",
            self.clear_chat
        )

        tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        ).pack(
            fill="both",
            expand=True
        )

        self.status_label = tk.Label(
            self.sidebar,
            text="● READY",
            bg=SIDEBAR,
            fg=ACCENT,
            font=("Segoe UI", 9)
        )

        self.status_label.pack(
            anchor="w",
            padx=20
        )

        tk.Label(
            self.sidebar,
            text="Groq • Desktop • Web • Chess",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            padx=20,
            pady=(5, 20)
        )

    def side_button(
        self,
        text,
        command
    ):

        tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            bg=SIDEBAR,
            fg=TEXT,
            activebackground="#292929",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=18,
            pady=11,
            font=("Segoe UI", 10),
            cursor="hand2"
        ).pack(
            fill="x",
            padx=8,
            pady=1
        )

    # ========================================================
    # MAIN AREA
    # ========================================================

    def build_main_area(self):

        self.main = tk.Frame(
            self.root,
            bg=BG
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True
        )

        header = tk.Frame(
            self.main,
            bg=BG,
            height=65
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        tk.Label(
            header,
            text="Autonomous Desktop AI",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(
            side="left",
            padx=22
        )

        tk.Label(
            header,
            text="● GROQ + TOOLS",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 9)
        ).pack(
            side="right",
            padx=22
        )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        chat_outer = tk.Frame(
            self.main,
            bg=BG
        )

        chat_outer.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            chat_outer,
            bg=BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            chat_outer,
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
            bg=BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.chat_frame,
            anchor="nw"
        )

        self.chat_frame.bind(
            "<Configure>",
            lambda event:
            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda event:
            self.canvas.itemconfigure(
                self.canvas_window,
                width=event.width
            )
        )

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        input_area = tk.Frame(
            self.main,
            bg=BG
        )

        input_area.pack(
            fill="x",
            padx=60,
            pady=(10, 5)
        )

        self.input_box = tk.Text(
            input_area,
            height=4,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 11),
            padx=14,
            pady=10
        )

        self.input_box.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.input_box.bind(
            "<Return>",
            self.handle_enter
        )

        button_area = tk.Frame(
            input_area,
            bg=BG
        )

        button_area.pack(
            side="right",
            fill="y",
            padx=(8, 0)
        )

        self.stop_button = tk.Button(
            button_area,
            text="■ STOP",
            command=self.stop,
            state="disabled",
            bg=DANGER,
            fg="white",
            activebackground="#C04B4B",
            relief="flat",
            bd=0,
            width=9,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )

        self.stop_button.pack(
            fill="x",
            pady=(0, 5)
        )

        self.send_button = tk.Button(
            button_area,
            text="➤ SEND",
            command=self.send,
            bg=ACCENT,
            fg="white",
            activebackground="#0D8E6F",
            relief="flat",
            bd=0,
            width=9,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )

        self.send_button.pack(
            fill="x"
        )

    # ========================================================
    # CHAT MESSAGE
    # ========================================================

    def add_message(
        self,
        speaker,
        text,
        animate=False
    ):

        text = str(text)

        self.messages.append(
            {
                "speaker": speaker,
                "text": text
            }
        )

        outer = tk.Frame(
            self.chat_frame,
            bg=BG
        )

        outer.pack(
            fill="x",
            padx=60,
            pady=10
        )

        top = tk.Frame(
            outer,
            bg=BG
        )

        top.pack(
            fill="x"
        )

        name = (
            "You"
            if speaker == "YOU"
            else "System"
            if speaker == "SYSTEM"
            else "Autonomous AI"
        )

        tk.Label(
            top,
            text=name,
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(
            side="left"
        )

        tk.Button(
            top,
            text="Copy",
            command=lambda value=text:
            self.copy_text(value),
            bg=BG,
            fg=MUTED,
            activebackground=BG,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8),
            cursor="hand2"
        ).pack(
            side="right"
        )

        card = tk.Frame(
            outer,
            bg=USER_BG if speaker == "YOU" else BG
        )

        card.pack(
            fill="x",
            pady=(4, 0)
        )

        label = tk.Label(
            card,
            text="",
            bg=USER_BG if speaker == "YOU" else BG,
            fg=TEXT,
            justify="left",
            anchor="w",
            wraplength=900,
            font=("Segoe UI", 11),
            padx=15,
            pady=13
        )

        label.pack(
            fill="x"
        )

        if animate and speaker == "AI":

            self.typewriter(
                label,
                text
            )

        else:

            label.configure(
                text=text
            )

        self.chat_widgets.append(
            outer
        )

        self.root.after(
            50,
            lambda:
            self.canvas.yview_moveto(1.0)
        )

    # ========================================================
    # TYPEWRITER
    # ========================================================

    def typewriter(
        self,
        label,
        text
    ):

        index = [0]

        def step():

            if index[0] >= len(text):
                return

            index[0] += 1

            label.configure(
                text=text[
                    :index[0]
                ]
            )

            self.root.after(
                8,
                step
            )

        step()

    # ========================================================
    # SEND
    # ========================================================

    def handle_enter(
        self,
        event
    ):

        # Shift+Enter = newline
        if event.state & 0x0001:
            return

        self.send()

        return "break"

    def send(self):

        if self.running:
            return

        message = self.input_box.get(
            "1.0",
            "end"
        ).strip()

        if not message:
            return

        self.input_box.delete(
            "1.0",
            "end"
        )

        self.add_message(
            "YOU",
            message
        )

        self.conversation.append(
            {
                "role": "user",
                "content": message
            }
        )

        self.running = True
        self.stop_event.clear()

        self.send_button.configure(
            state="disabled",
            text="WORKING..."
        )

        self.stop_button.configure(
            state="normal"
        )

        self.status_label.configure(
            text="● WORKING",
            fg="#F0C674"
        )

        threading.Thread(
            target=self.ai_worker,
            args=(message,),
            daemon=True
        ).start()

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        if not self.running:
            return

        self.stop_event.set()

        self.status_label.configure(
            text="● STOP REQUESTED",
            fg="#F0C674"
        )

        self.stop_button.configure(
            state="disabled"
        )

    # ========================================================
    # APPROVAL
    # ========================================================

    def approve_action(
        self,
        action,
        details
    ):

        result = {
            "approved": False
        }

        event = threading.Event()

        def dialog():

            window = tk.Toplevel(
                self.root
            )

            window.title(
                "Owner Approval"
            )

            window.geometry(
                "520x350"
            )

            window.configure(
                bg="#181818"
            )

            window.transient(
                self.root
            )

            window.grab_set()

            tk.Label(
                window,
                text="🔐 OWNER APPROVAL",
                bg="#181818",
                fg=TEXT,
                font=("Segoe UI", 16, "bold")
            ).pack(
                pady=(25, 12)
            )

            tk.Label(
                window,
                text=(
                    str(action)
                    + "\n\n"
                    + str(details)
                ),
                bg="#181818",
                fg=MUTED,
                wraplength=430,
                justify="center"
            ).pack(
                pady=8
            )

            entry = tk.Entry(
                window,
                show="●",
                bg="#2C2C2C",
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                justify="center",
                font=("Segoe UI", 12)
            )

            entry.pack(
                padx=60,
                fill="x",
                ipady=10
            )

            entry.focus_force()

            def accept():

                if entry.get() == ACTION_PASSWORD:

                    result["approved"] = True

                    window.grab_release()
                    window.destroy()
                    event.set()

                else:

                    entry.delete(
                        0,
                        "end"
                    )

                    messagebox.showerror(
                        "Access Denied",
                        "Incorrect action password.",
                        parent=window
                    )

            def reject():

                window.grab_release()
                window.destroy()
                event.set()

            row = tk.Frame(
                window,
                bg="#181818"
            )

            row.pack(
                fill="x",
                padx=60,
                pady=20
            )

            tk.Button(
                row,
                text="CANCEL",
                command=reject,
                bg="#3A3A3A",
                fg=TEXT,
                relief="flat",
                bd=0,
                padx=20,
                pady=9
            ).pack(
                side="left"
            )

            tk.Button(
                row,
                text="AUTHORIZE",
                command=accept,
                bg=ACCENT,
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=9
            ).pack(
                side="right"
            )

            window.protocol(
                "WM_DELETE_WINDOW",
                reject
            )

        self.root.after(
            0,
            dialog
        )

        event.wait()

        return result

    # ========================================================
    # AI WORKER
    # ========================================================

    def ai_worker(
        self,
        message
    ):

        answer = None

        try:

            if self.stop_event.is_set():

                answer = "Task stopped."

            elif RealGroqAgent is None:

                raise RuntimeError(
                    "RealGroqAgent could not be imported."
                )

            elif ToolRegistry is None:

                raise RuntimeError(
                    "ToolRegistry could not be imported."
                )

            else:

                registry = ToolRegistry(
                    self.approve_action
                )

                # Support different versions of the existing agent.
                agent = None

                constructors = [
                    lambda:
                    RealGroqAgent(
                        registry,
                        self.stop_event
                    ),
                    lambda:
                    RealGroqAgent(
                        registry
                    ),
                    lambda:
                    RealGroqAgent()
                ]

                last_error = None

                for create in constructors:

                    try:

                        agent = create()
                        break

                    except TypeError as exc:

                        last_error = exc

                if agent is None:

                    raise RuntimeError(
                        "Could not initialize RealGroqAgent: "
                        + str(last_error)
                    )

                # Support common method names used by the
                # different generations of your agent.

                if hasattr(agent, "run"):

                    try:

                        answer = agent.run(
                            message,
                            self.conversation
                        )

                    except TypeError:

                        answer = agent.run(
                            message
                        )

                elif hasattr(agent, "chat"):

                    try:

                        answer = agent.chat(
                            message,
                            self.conversation
                        )

                    except TypeError:

                        answer = agent.chat(
                            message
                        )

                elif hasattr(agent, "execute"):

                    answer = agent.execute(
                        message
                    )

                else:

                    raise RuntimeError(
                        "RealGroqAgent has no supported "
                        "run/chat/execute method."
                    )

        except Exception as exc:

            answer = (
                "I couldn't complete the request.\n\n"
                + str(exc)
            )

        if self.stop_event.is_set():

            answer = "Task stopped by user."

        self.root.after(
            0,
            lambda:
            self.finish_answer(
                str(answer)
            )
        )

    # ========================================================
    # FINISH
    # ========================================================

    def finish_answer(
        self,
        answer
    ):

        self.conversation.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        self.add_message(
            "AI",
            answer,
            animate=True
        )

        self.running = False
        self.stop_event.clear()

        self.send_button.configure(
            state="normal",
            text="➤ SEND"
        )

        self.stop_button.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="● READY",
            fg=ACCENT
        )

    # ========================================================
    # COPY
    # ========================================================

    def copy_text(
        self,
        text
    ):

        try:

            self.root.clipboard_clear()
            self.root.clipboard_append(
                str(text)
            )

            self.root.update()

            self.status_label.configure(
                text="● COPIED",
                fg=ACCENT
            )

            self.root.after(
                1200,
                lambda:
                self.status_label.configure(
                    text="● READY",
                    fg=ACCENT
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "Copy",
                str(exc)
            )

    def copy_conversation(self):

        if not self.messages:
            return

        transcript = "\n\n".join(
            item["speaker"]
            + ":\n"
            + item["text"]
            for item in self.messages
        )

        self.copy_text(
            transcript
        )

    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self):

        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        self.messages.clear()
        self.conversation.clear()

        self.add_message(
            "AI",
            "New conversation started."
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_chat(self):

        if not messagebox.askyesno(
            "Clear Conversation",
            "Clear this conversation?"
        ):
            return

        self.new_chat()

    # ========================================================
    # UPLOAD
    # ========================================================

    def upload(self):

        files = filedialog.askopenfilenames(
            title="Upload files"
        )

        if not files:
            return

        copied = []

        for source in files:

            try:

                filename = os.path.basename(
                    source
                )

                destination = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                base, ext = os.path.splitext(
                    filename
                )

                counter = 1

                while os.path.exists(
                    destination
                ):

                    destination = os.path.join(
                        UPLOAD_DIR,
                        f"{base}_{counter}{ext}"
                    )

                    counter += 1

                shutil.copy2(
                    source,
                    destination
                )

                copied.append(
                    destination
                )

            except Exception as exc:

                self.add_message(
                    "SYSTEM",
                    "Upload failed:\n" + str(exc)
                )

        if copied:

            self.add_message(
                "SYSTEM",
                "Uploaded successfully:\n\n"
                + "\n".join(copied)
            )

            self.input_box.insert(
                "end",
                "\nAnalyze the uploaded files."
            )

    # ========================================================
    # CHESS
    # ========================================================

    def open_chess(self):

        try:

            from agent.stockfish_chess import launch

            launch(
                self.root
            )

        except Exception as exc:

            messagebox.showerror(
                "Stockfish Chess",
                (
                    "Chess could not be opened.\n\n"
                    + str(exc)
                )
            )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        self.root.mainloop()


# ============================================================
# ENTRY POINT
# ============================================================

def launch():

    app = AutonomousDesktopAI()

    app.run()


if __name__ == "__main__":

    launch()

import os
import json
import uuid
from datetime import datetime

# ============================================================
# PERSISTENT CHAT HISTORY
# ============================================================

_HISTORY_DIR = os.path.join(
    ROOT,
    "data",
    "chat_history"
)

_HISTORY_FILE = os.path.join(
    _HISTORY_DIR,
    "history.json"
)

os.makedirs(
    _HISTORY_DIR,
    exist_ok=True
)


def _clean_ai_text(text):
    """Repair common Windows UTF-8/mojibake output."""

    text = str(text)

    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
        "Â ": " ",
        "Â": "",
        "ðŸ˜Š": ":)",
        "ðŸ˜‚": ":D",
        "ðŸ‘": "",
        "�": "",
    }

    for bad, good in replacements.items():
        text = text.replace(
            bad,
            good
        )

    return "".join(
        ch
        for ch in text
        if ch in "\n\t\r" or ord(ch) >= 32
    )


def _load_saved_chats():
    try:

        if not os.path.exists(
            _HISTORY_FILE
        ):
            return {}

        with open(
            _HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as exc:

        print(
            "History load warning:",
            exc
        )

    return {}


def _write_saved_chats(data):
    try:

        tmp = _HISTORY_FILE + ".tmp"

        with open(
            tmp,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        os.replace(
            tmp,
            _HISTORY_FILE
        )

    except Exception as exc:

        print(
            "History save warning:",
            exc
        )


# ============================================================
# ORIGINAL METHODS
# ============================================================

_original_app_init = AutonomousDesktopAI.__init__
_original_add_message = AutonomousDesktopAI.add_message
_original_new_chat = AutonomousDesktopAI.new_chat


# ============================================================
# HISTORY UI
# ============================================================

def _history_title(messages):

    for item in messages:

        if item.get("speaker") == "YOU":

            text = _clean_ai_text(
                item.get("text", "")
            )

            text = " ".join(
                text.split()
            )

            if text:

                if len(text) > 38:
                    return text[:38] + "..."

                return text

    return "New conversation"


def _install_history(self):

    self._saved_chats = _load_saved_chats()

    if not getattr(
        self,
        "chat_id",
        None
    ):

        self.chat_id = str(
            uuid.uuid4()
        )

    if not getattr(
        self,
        "chat_title",
        None
    ):

        self.chat_title = "New conversation"

    # Create history area if sidebar exists.
    if hasattr(
        self,
        "sidebar"
    ):

        tk.Label(
            self.sidebar,
            text="CHAT HISTORY",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 6)
        )

        self.history_frame = tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        )

        self.history_frame.pack(
            fill="x",
            padx=8
        )

    self._save_current_chat()
    self._refresh_history()


def _save_current_chat(self):

    try:

        messages = getattr(
            self,
            "messages",
            []
        )

        conversation = getattr(
            self,
            "conversation",
            []
        )

        if not messages:
            return

        title = self.chat_title

        if (
            not title
            or
            title == "New conversation"
        ):

            title = _history_title(
                messages
            )

        self.chat_title = title

        self._saved_chats[
            self.chat_id
        ] = {
            "title": title,
            "updated": datetime.now().isoformat(),
            "messages": [
                {
                    "speaker": _clean_ai_text(
                        item.get(
                            "speaker",
                            ""
                        )
                    ),
                    "text": _clean_ai_text(
                        item.get(
                            "text",
                            ""
                        )
                    )
                }
                for item in messages
            ],
            "conversation": conversation
        }

        _write_saved_chats(
            self._saved_chats
        )

    except Exception as exc:

        print(
            "History save warning:",
            exc
        )


def _refresh_history(self):

    frame = getattr(
        self,
        "history_frame",
        None
    )

    if frame is None:
        return

    for widget in frame.winfo_children():
        widget.destroy()

    chats = sorted(
        self._saved_chats.items(),
        key=lambda item:
        item[1].get(
            "updated",
            ""
        ),
        reverse=True
    )

    for chat_id, data in chats[:30]:

        title = data.get(
            "title",
            "Conversation"
        )

        row = tk.Frame(
            frame,
            bg="#242424"
        )

        row.pack(
            fill="x",
            pady=1
        )

        tk.Button(
            row,
            text=title,
            anchor="w",
            command=lambda cid=chat_id:
            self._open_saved_chat(cid),
            bg="#242424",
            fg=TEXT,
            activebackground="#303030",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 9)
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Button(
            row,
            text="X",
            command=lambda cid=chat_id:
            self._delete_saved_chat(cid),
            bg="#242424",
            fg=MUTED,
            activebackground="#492626",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2"
        ).pack(
            side="right"
        )


def _open_saved_chat(self, chat_id):

    data = self._saved_chats.get(
        chat_id
    )

    if not data:
        return

    if getattr(
        self,
        "running",
        False
    ):

        self.stop()

    self.chat_id = chat_id

    self.chat_title = data.get(
        "title",
        "Conversation"
    )

    self.messages = list(
        data.get(
            "messages",
            []
        )
    )

    self.conversation = list(
        data.get(
            "conversation",
            []
        )
    )

    if not hasattr(
        self,
        "chat_frame"
    ):
        return

    for widget in self.chat_frame.winfo_children():
        widget.destroy()

    for item in self.messages:

        self._original_history_add(
            item.get(
                "speaker",
                "AI"
            ),
            _clean_ai_text(
                item.get(
                    "text",
                    ""
                )
            ),
            False
        )

    self._refresh_history()

    self._scroll_to_bottom()


def _delete_saved_chat(self, chat_id):

    if chat_id not in self._saved_chats:
        return

    if not messagebox.askyesno(
        "Delete Conversation",
        "Delete this conversation?"
    ):
        return

    del self._saved_chats[
        chat_id
    ]

    _write_saved_chats(
        self._saved_chats
    )

    if chat_id == self.chat_id:

        self.chat_id = str(
            uuid.uuid4()
        )

        self.chat_title = (
            "New conversation"
        )

        self.messages = []
        self.conversation = []

        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        self._original_history_add(
            "AI",
            "New conversation started.",
            False
        )

    self._refresh_history()


# ============================================================
# AUTO SCROLL
# ============================================================

def _scroll_to_bottom(self):

    try:

        self.canvas.update_idletasks()

        self.canvas.yview_moveto(
            1.0
        )

    except Exception:
        pass


def _better_typewriter(
    self,
    label,
    text
):

    text = _clean_ai_text(
        text
    )

    index = [0]

    def step():

        try:

            if not label.winfo_exists():
                return

            if index[0] >= len(text):

                self._scroll_to_bottom()

                return

            # Smooth but efficient typing.
            index[0] += min(
                3,
                len(text) - index[0]
            )

            label.configure(
                text=text[
                    :index[0]
                ]
            )

            # LIVE scroll exactly like a chat interface.
            self._scroll_to_bottom()

            self.root.after(
                10,
                step
            )

        except Exception:
            return

    step()


# ============================================================
# MESSAGE WRAPPER
# ============================================================

def _better_add_message(
    self,
    speaker,
    text,
    *args,
    **kwargs
):

    text = _clean_ai_text(
        text
    )

    result = self._original_history_add(
        speaker,
        text,
        *args,
        **kwargs
    )

    try:

        self._save_current_chat()

        self.root.after(
            20,
            self._scroll_to_bottom
        )

    except Exception:
        pass

    return result


# ============================================================
# NEW CHAT WRAPPER
# ============================================================

def _better_new_chat(self):

    try:
        self._save_current_chat()
    except Exception:
        pass

    self.chat_id = str(
        uuid.uuid4()
    )

    self.chat_title = (
        "New conversation"
    )

    result = self._original_history_new_chat()

    try:

        self._save_current_chat()
        self._refresh_history()
        self._scroll_to_bottom()

    except Exception:
        pass

    return result


# ============================================================
# INITIALIZATION WRAPPER
# ============================================================

def _better_init(
    self,
    *args,
    **kwargs
):

    self.chat_id = str(
        uuid.uuid4()
    )

    self.chat_title = (
        "New conversation"
    )

    self._saved_chats = {}

    self._original_history_add = (
        _original_add_message.__get__(
            self,
            AutonomousDesktopAI
        )
    )

    self._original_history_new_chat = (
        _original_new_chat.__get__(
            self,
            AutonomousDesktopAI
        )
    )

    _original_app_init(
        self,
        *args,
        **kwargs
    )

    # Install after original dashboard UI exists.
    self._install_history()


# ============================================================
# INSTALL
# ============================================================

AutonomousDesktopAI.__init__ = _better_init
AutonomousDesktopAI.add_message = _better_add_message
AutonomousDesktopAI.new_chat = _better_new_chat
AutonomousDesktopAI.typewriter = _better_typewriter

AutonomousDesktopAI._install_history = _install_history
AutonomousDesktopAI._save_current_chat = _save_current_chat
AutonomousDesktopAI._refresh_history = _refresh_history
AutonomousDesktopAI._open_saved_chat = _open_saved_chat
AutonomousDesktopAI._delete_saved_chat = _delete_saved_chat
AutonomousDesktopAI._scroll_to_bottom = _scroll_to_bottom


# ============================================================
# CLEAN AI OUTPUT AT FINISH
# ============================================================

_original_finish = getattr(
    AutonomousDesktopAI,
    "finish_answer",
    None
)

if _original_finish:

    def _clean_finish(
        self,
        answer
    ):

        answer = _clean_ai_text(
            answer
        )

        return _original_finish(
            self,
            answer
        )

    AutonomousDesktopAI.finish_answer = (
        _clean_finish
    )

print(
    "ALL 3 UI UPGRADES INSTALLED"
)
