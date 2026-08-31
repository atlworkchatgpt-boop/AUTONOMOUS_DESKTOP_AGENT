
# ============================================================
# AUTONOMOUS DESKTOP AI
# CHATGPT-STYLE WINDOWS DASHBOARD
# GEMINI 3.7 FLASH INTEGRATION
# ============================================================

import os
import sys
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# ============================================================
# PYTHON / PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

# ============================================================
# GEMINI
# ============================================================

try:
    import litellm
    LITELLM_AVAILABLE = True
    LITELLM_ERROR = ""
except Exception as e:
    litellm = None
    LITELLM_AVAILABLE = False
    LITELLM_ERROR = str(e)

GEMINI_MODEL = "gemini/gemini-3.7-flash"

# ============================================================
# UPLOAD DIRECTORY
# ============================================================

try:
    from agent.config import UPLOAD_DIR
except Exception:
    UPLOAD_DIR = os.path.join(
        PROJECT_ROOT,
        "uploads"
    )

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

# ============================================================
# COLORS
# ============================================================

BG = "#212121"
SIDEBAR = "#171717"
CHAT_BG = "#212121"
INPUT_BG = "#2f2f2f"
BORDER = "#3d3d3d"
TEXT = "#ececec"
MUTED = "#a0a0a0"
ACCENT = "#10a37f"
HOVER = "#2a2a2a"
USER_BG = "#2f2f2f"
AI_BG = "#212121"

# ============================================================
# DASHBOARD
# ============================================================


class Dashboard:

    def __init__(self, root):

        self.root = root

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

        self.busy = False

        self.messages = []

        self.conversation = []

        self.build_styles()
        self.build_ui()

        # IMPORTANT:
        # Never initialize AI before the GUI exists.
        self.root.after(
            500,
            self.check_gemini
        )

    # ========================================================
    # STYLES
    # ========================================================

    def build_styles(self):

        style = tk.ttk.Style()

        try:
            style.theme_use("clam")
        except Exception:
            pass

    # ========================================================
    # MAIN UI
    # ========================================================

    def build_ui(self):

        self.main = tk.Frame(
            self.root,
            bg=BG
        )

        self.main.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = tk.Frame(
            self.main,
            bg=SIDEBAR,
            width=250
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="◉  AUTONOMOUS AI",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(22, 20)
        )

        self.sidebar_button(
            "＋  New chat",
            self.new_chat
        )

        self.sidebar_button(
            "♟  Chess",
            self.open_chess
        )

        self.sidebar_button(
            "📁  Files",
            self.upload
        )

        self.sidebar_button(
            "🎙  Voice",
            self.record_audio
        )

        self.sidebar_button(
            "📋  Copy conversation",
            self.copy_chat
        )

        self.sidebar_button(
            "🗑  Clear",
            self.clear_chat
        )

        tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        ).pack(
            fill="both",
            expand=True
        )

        self.sidebar_status = tk.Label(
            self.sidebar,
            text="● STARTING",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 9)
        )

        self.sidebar_status.pack(
            anchor="w",
            padx=20,
            pady=(0, 5)
        )

        tk.Label(
            self.sidebar,
            text="Gemini 3.7 Flash • Autonomous AI",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 20)
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content = tk.Frame(
            self.main,
            bg=CHAT_BG
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # HEADER
        # ====================================================

        self.header = tk.Frame(
            self.content,
            bg=CHAT_BG,
            height=62
        )

        self.header.pack(
            fill="x"
        )

        self.header.pack_propagate(False)

        tk.Label(
            self.header,
            text="Autonomous Desktop AI",
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(
            side="left",
            padx=22
        )

        self.model_label = tk.Label(
            self.header,
            text="Checking Gemini...",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        )

        self.model_label.pack(
            side="right",
            padx=22
        )

        # ====================================================
        # CHAT
        # ====================================================

        chat_container = tk.Frame(
            self.content,
            bg=CHAT_BG
        )

        chat_container.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            chat_container,
            bg=CHAT_BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            chat_container,
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

        self.canvas_window = self.canvas.create_window(
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

        # ====================================================
        # INPUT
        # ====================================================

        input_outer = tk.Frame(
            self.content,
            bg=CHAT_BG
        )

        input_outer.pack(
            fill="x",
            padx=90,
            pady=(10, 8)
        )

        self.input_box = tk.Text(
            input_outer,
            height=3,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            wrap="word",
            font=("Segoe UI", 11),
            padx=15,
            pady=12
        )

        self.input_box.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.input_box.bind(
            "<Control-Return>",
            lambda e: self.send()
        )

        self.input_box.bind(
            "<Return>",
            self.enter_handler
        )

        self.send_button = tk.Button(
            input_outer,
            text="➤",
            command=self.send,
            bg=ACCENT,
            fg="white",
            activebackground="#0d8f70",
            activeforeground="white",
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

        # ====================================================
        # BOTTOM BUTTONS
        # ====================================================

        bottom = tk.Frame(
            self.content,
            bg=CHAT_BG
        )

        bottom.pack(
            fill="x",
            padx=90,
            pady=(0, 5)
        )

        self.small_button(
            bottom,
            "📎",
            self.upload
        ).pack(
            side="left",
            padx=3
        )

        self.small_button(
            bottom,
            "🎙",
            self.record_audio
        ).pack(
            side="left",
            padx=3
        )

        tk.Label(
            bottom,
            text="Enter to send • Shift+Enter for new line",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            side="right"
        )

        tk.Label(
            self.content,
            text="Autonomous Desktop AI • Gemini-powered",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            pady=(0, 8)
        )

        # ====================================================
        # WELCOME
        # ====================================================

        self.add_message(
            "AI",
            "Hey! I'm your Autonomous Desktop AI.\n\n"
            "I'm powered by Gemini 3.7 Flash.\n\n"
            "I can:\n"
            "• Answer questions\n"
            "• Reason through problems\n"
            "• Remember the current conversation\n"
            "• Analyze uploaded files\n"
            "• Help with your projects\n"
            "• Play chess\n\n"
            "Ask me anything."
        )

    # ========================================================
    # BUTTONS
    # ========================================================

    def sidebar_button(
        self,
        text,
        command
    ):

        button = tk.Button(
            self.sidebar,
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

    def small_button(
        self,
        parent,
        text,
        command
    ):

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
            font=("Segoe UI", 12),
            cursor="hand2"
        )

    # ========================================================
    # RESIZE
    # ========================================================

    def resize_chat(self, event):

        try:
            self.canvas.itemconfig(
                self.canvas_window,
                width=event.width
            )
        except Exception:
            pass

    # ========================================================
    # GEMINI CHECK
    # ========================================================

    def check_gemini(self):

        if not LITELLM_AVAILABLE:

            self.model_label.configure(
                text="LiteLLM unavailable",
                fg="#ff6b6b"
            )

            self.sidebar_status.configure(
                text="● AI ERROR",
                fg="#ff6b6b"
            )

            self.add_message(
                "SYSTEM",
                "LiteLLM could not be imported:\n\n"
                + LITELLM_ERROR
            )

            return

        if not os.environ.get("GEMINI_API_KEY"):

            self.model_label.configure(
                text="Gemini key missing",
                fg="#ff6b6b"
            )

            self.sidebar_status.configure(
                text="● NO KEY",
                fg="#ff6b6b"
            )

            self.add_message(
                "SYSTEM",
                "GEMINI_API_KEY was not found."
            )

            return

        self.model_label.configure(
            text="● Gemini 3.7 Flash",
            fg=ACCENT
        )

        self.sidebar_status.configure(
            text="● READY",
            fg=ACCENT
        )

    # ========================================================
    # MESSAGE
    # ========================================================

    def add_message(
        self,
        speaker,
        text
    ):

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
            padx=75,
            pady=13
        )

        if speaker == "YOU":

            bubble_bg = USER_BG
            name = "You"

        elif speaker == "SYSTEM":

            bubble_bg = SIDEBAR
            name = "System"

        else:

            bubble_bg = AI_BG
            name = "Autonomous AI"

        name_row = tk.Frame(
            outer,
            bg=CHAT_BG
        )

        name_row.pack(
            fill="x"
        )

        tk.Label(
            name_row,
            text=name,
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(
            side="left"
        )

        copy_button = tk.Button(
            name_row,
            text="Copy",
            command=lambda t=text: self.copy_text(t),
            bg=CHAT_BG,
            fg=MUTED,
            activebackground=HOVER,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 8),
            cursor="hand2"
        )

        copy_button.pack(
            side="right"
        )

        bubble = tk.Frame(
            outer,
            bg=bubble_bg
        )

        bubble.pack(
            fill="x",
            pady=(5, 0)
        )

        label = tk.Label(
            bubble,
            text=text,
            bg=bubble_bg,
            fg=TEXT,
            justify="left",
            anchor="w",
            wraplength=850,
            font=("Segoe UI", 11),
            padx=14,
            pady=12
        )

        label.pack(
            fill="x"
        )

        self.root.after(
            50,
            lambda: self.canvas.yview_moveto(1.0)
        )

    # ========================================================
    # SEND
    # ========================================================

    def enter_handler(
        self,
        event
    ):

        # Shift+Enter = newline
        if event.state & 0x0001:
            return

        self.send()

        return "break"

    def send(self):

        if self.busy:
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

        # Save conversation history for Gemini
        self.conversation.append(
            {
                "role": "user",
                "content": message
            }
        )

        if not LITELLM_AVAILABLE:

            self.add_message(
                "SYSTEM",
                "LiteLLM is unavailable."
            )

            return

        if not os.environ.get("GEMINI_API_KEY"):

            self.add_message(
                "SYSTEM",
                "GEMINI_API_KEY is missing."
            )

            return

        self.busy = True

        self.send_button.configure(
            state="disabled",
            text="…"
        )

        self.sidebar_status.configure(
            text="● THINKING...",
            fg="#f0c674"
        )

        threading.Thread(
            target=self.gemini_worker,
            args=(message,),
            daemon=True
        ).start()

    # ========================================================
    # GEMINI WORKER
    # ========================================================

    def gemini_worker(
        self,
        message
    ):

        try:

            response = litellm.completion(
                model=GEMINI_MODEL,
                messages=self.conversation,
                api_key=os.environ.get(
                    "GEMINI_API_KEY"
                ),
                temperature=0.7
            )

            answer = (
                response
                .choices[0]
                .message
                .content
            )

            if not answer:
                answer = "Gemini returned an empty response."

            answer = str(answer)

        except Exception as e:

            answer = (
                "Gemini request failed.\n\n"
                + str(e)
            )

        self.root.after(
            0,
            lambda: self.finish_response(answer)
        )

    # ========================================================
    # FINISH RESPONSE
    # ========================================================

    def finish_response(
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
            answer
        )

        self.busy = False

        self.send_button.configure(
            state="normal",
            text="➤"
        )

        self.sidebar_status.configure(
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
                text
            )

            self.root.update()

            self.sidebar_status.configure(
                text="● COPIED",
                fg=ACCENT
            )

            self.root.after(
                1200,
                lambda: self.sidebar_status.configure(
                    text="● READY",
                    fg=ACCENT
                )
            )

        except Exception as e:

            messagebox.showerror(
                "Copy error",
                str(e)
            )

    def copy_chat(self):

        if not self.messages:
            return

        parts = []

        for msg in self.messages:

            parts.append(
                msg["speaker"]
                + ":\n"
                + msg["text"]
            )

        self.copy_text(
            "\n\n".join(parts)
        )

    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self):

        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        self.messages = []
        self.conversation = []

        self.add_message(
            "AI",
            "New conversation started. What would you like to do?"
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_chat(self):

        if not self.messages:
            return

        if not messagebox.askyesno(
            "Clear conversation",
            "Clear the current conversation?"
        ):
            return

        self.new_chat()

    # ========================================================
    # UPLOAD
    # ========================================================

    def upload(self):

        paths = filedialog.askopenfilenames(
            title="Upload files"
        )

        if not paths:
            return

        uploaded = []

        for source in paths:

            try:

                filename = os.path.basename(
                    source
                )

                destination = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                if os.path.exists(destination):

                    base, ext = os.path.splitext(
                        filename
                    )

                    i = 1

                    while os.path.exists(
                        destination
                    ):

                        destination = os.path.join(
                            UPLOAD_DIR,
                            f"{base}_{i}{ext}"
                        )

                        i += 1

                shutil.copy2(
                    source,
                    destination
                )

                uploaded.append(
                    destination
                )

            except Exception as e:

                self.add_message(
                    "SYSTEM",
                    "Upload failed:\n"
                    + str(e)
                )

        if uploaded:

            text = (
                "Uploaded successfully:\n\n"
                + "\n".join(uploaded)
            )

            self.add_message(
                "SYSTEM",
                text
            )

            self.input_box.insert(
                "end",
                "\nAnalyze the uploaded files if relevant."
            )

    # ========================================================
    # VOICE
    # ========================================================

    def record_audio(self):

        self.add_message(
            "SYSTEM",
            "Voice mode is not connected yet."
        )

    # ========================================================
    # CHESS
    # ========================================================

    def open_chess(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Autonomous AI — Chess"
        )

        window.geometry(
            "760x720"
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
            pady=(18, 4)
        )

        tk.Label(
            window,
            text="Interactive board",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(
            pady=(0, 12)
        )

        board_frame = tk.Frame(
            window,
            bg=BG
        )

        board_frame.pack()

        board_size = 560
        square = board_size // 8

        canvas = tk.Canvas(
            board_frame,
            width=board_size,
            height=board_size,
            highlightthickness=0,
            bg="#eee"
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

            canvas.delete("all")

            for r in range(8):

                for c in range(8):

                    x1 = c * square
                    y1 = r * square
                    x2 = x1 + square
                    y2 = y1 + square

                    light = (
                        (r + c) % 2 == 0
                    )

                    canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill="#f0d9b5" if light else "#b58863",
                        outline=""
                    )

                    piece = pieces[r][c]

                    if piece:

                        canvas.create_text(
                            x1 + square / 2,
                            y1 + square / 2,
                            text=piece,
                            font=("Segoe UI Symbol", 42),
                            fill="#111111"
                        )

            if selected[0]:

                r, c = selected[0]

                canvas.create_rectangle(
                    c * square,
                    r * square,
                    (c + 1) * square,
                    (r + 1) * square,
                    outline=ACCENT,
                    width=5
                )

        def click(event):

            c = event.x // square
            r = event.y // square

            if not (0 <= r < 8 and 0 <= c < 8):
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
            text="Gemini can be used separately to analyze chess positions.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(
            pady=12
        )


# ============================================================
# LAUNCH
# ============================================================

def launch():

    root = tk.Tk()

    Dashboard(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    launch()

 