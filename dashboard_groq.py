import os
import sys
import threading
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

ROOT = os.path.dirname(os.path.abspath(__file__))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.chdir(ROOT)

from groq_backend_new import GroqBrain

# ============================================================
# COLORS
# ============================================================

BG = "#212121"
SIDEBAR = "#171717"
CHAT_BG = "#212121"
INPUT_BG = "#2f2f2f"
TEXT = "#ececec"
MUTED = "#a0a0a0"
ACCENT = "#10a37f"
HOVER = "#2a2a2a"
USER_BG = "#2f2f2f"
AI_BG = "#212121"

UPLOAD_DIR = os.path.join(ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class Dashboard:

    def __init__(self, root):

        self.root = root

        self.root.title("Autonomous Desktop AI")
        self.root.geometry("1280x820")
        self.root.minsize(950, 650)
        self.root.configure(bg=BG)

        self.busy = False
        self.messages = []
        self.conversation = []

        try:
            self.brain = GroqBrain()
            self.ai_ready = True
        except Exception as e:
            self.brain = None
            self.ai_ready = False
            self.ai_error = str(e)

        self.build_ui()

        if self.ai_ready:
            self.model_label.configure(
                text="● Groq Compound • Live Web",
                fg=ACCENT
            )
            self.status("● READY", ACCENT)
        else:
            self.model_label.configure(
                text="Groq unavailable",
                fg="#ff6b6b"
            )
            self.status("● AI ERROR", "#ff6b6b")

            self.add_message(
                "SYSTEM",
                "Groq could not start:\n\n" + self.ai_error
            )

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        sidebar = tk.Frame(
            main,
            bg=SIDEBAR,
            width=250
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="◉  AUTONOMOUS AI",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", padx=20, pady=(22, 20))

        self.sidebar_button(
            sidebar, "＋  New chat", self.new_chat
        )

        self.sidebar_button(
            sidebar, "♟  Chess", self.open_chess
        )

        self.sidebar_button(
            sidebar, "📁  Files", self.upload
        )

        self.sidebar_button(
            sidebar, "🖥  Computer tools", self.show_tools
        )

        self.sidebar_button(
            sidebar, "📋  Copy conversation", self.copy_chat
        )

        self.sidebar_button(
            sidebar, "🗑  Clear", self.clear_chat
        )

        tk.Frame(
            sidebar,
            bg=SIDEBAR
        ).pack(fill="both", expand=True)

        self.sidebar_status = tk.Label(
            sidebar,
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
            sidebar,
            text="Groq Compound • Live information",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w", padx=20, pady=(0, 20))

        content = tk.Frame(main, bg=CHAT_BG)
        content.pack(side="left", fill="both", expand=True)

        header = tk.Frame(
            content,
            bg=CHAT_BG,
            height=62
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Autonomous Desktop AI",
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(side="left", padx=22)

        self.model_label = tk.Label(
            header,
            text="Starting...",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.model_label.pack(side="right", padx=22)

        container = tk.Frame(content, bg=CHAT_BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            container,
            bg=CHAT_BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

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

        input_outer = tk.Frame(
            content,
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
            relief="flat",
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
            padx=90,
            pady=(0, 5)
        )

        self.small_button(
            bottom, "📎", self.upload
        ).pack(side="left", padx=3)

        tk.Label(
            bottom,
            text="Enter = send • Shift+Enter = new line",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(side="right")

        tk.Label(
            content,
            text="Groq-powered • current-information capable",
            bg=CHAT_BG,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(pady=(0, 8))

        self.add_message(
            "AI",
            "Hey! I'm your Groq-powered Autonomous Desktop AI.\n\n"
            "I can answer questions, use current web information, "
            "work with uploaded files, maintain the conversation, "
            "and connect to your existing desktop tools.\n\n"
            "Ask me something."
        )

    def sidebar_button(self, parent, text, command):

        b = tk.Button(
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

        b.pack(fill="x", padx=8, pady=1)
        return b

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
            font=("Segoe UI", 12),
            cursor="hand2"
        )

    def status(self, text, color):

        self.sidebar_status.configure(
            text=text,
            fg=color
        )

    def resize_chat(self, event):

        try:
            self.canvas.itemconfig(
                self.canvas_window,
                width=event.width
            )
        except Exception:
            pass

    # ========================================================
    # MESSAGES
    # ========================================================

    def add_message(self, speaker, text):

        self.messages.append({
            "speaker": speaker,
            "text": text
        })

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

        tk.Label(
            outer,
            text=name,
            bg=CHAT_BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

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
        label.pack(fill="x")

        self.root.after(
            50,
            lambda: self.canvas.yview_moveto(1.0)
        )

    # ========================================================
    # SEND
    # ========================================================

    def enter_handler(self, event):

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

        self.add_message("YOU", message)

        self.conversation.append({
            "role": "user",
            "content": message
        })

        if not self.ai_ready:
            self.add_message(
                "SYSTEM",
                "Groq is not ready."
            )
            return

        self.busy = True

        self.send_button.configure(
            state="disabled",
            text="…"
        )

        self.status(
            "● WORKING...",
            "#f0c674"
        )

        threading.Thread(
            target=self.worker,
            args=(message,),
            daemon=True
        ).start()

    def worker(self, message):

        try:

            answer = self.brain.ask(
                self.conversation[:-1],
                message
            )

        except Exception as e:

            answer = (
                "Groq request failed:\n\n"
                + str(e)
            )

        self.root.after(
            0,
            lambda: self.finish(answer)
        )

    def finish(self, answer):

        self.conversation.append({
            "role": "assistant",
            "content": answer
        })

        self.add_message("AI", answer)

        self.busy = False

        self.send_button.configure(
            state="normal",
            text="➤"
        )

        self.status(
            "● READY",
            ACCENT
        )

    # ========================================================
    # FILES
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

                filename = os.path.basename(source)
                destination = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                counter = 1

                while os.path.exists(destination):

                    base, ext = os.path.splitext(filename)

                    destination = os.path.join(
                        UPLOAD_DIR,
                        f"{base}_{counter}{ext}"
                    )

                    counter += 1

                shutil.copy2(
                    source,
                    destination
                )

                uploaded.append(destination)

            except Exception as e:

                self.add_message(
                    "SYSTEM",
                    "Upload failed:\n" + str(e)
                )

        if uploaded:

            text = (
                "Files uploaded:\n\n"
                + "\n".join(uploaded)
                + "\n\n"
                "You can now tell me what you want to do "
                "with these files."
            )

            self.add_message(
                "SYSTEM",
                text
            )

    # ========================================================
    # COMPUTER TOOLS
    # ========================================================

    def show_tools(self):

        tools_dir = os.path.join(ROOT, "tools")

        if not os.path.isdir(tools_dir):

            messagebox.showerror(
                "Tools",
                "tools folder was not found."
            )
            return

        files = []

        for name in sorted(os.listdir(tools_dir)):

            if name.endswith(".py"):
                files.append(name)

        messagebox.showinfo(
            "Existing Desktop Tools",
            "\n".join(files)
        )

    # ========================================================
    # COPY
    # ========================================================

    def copy_text(self, text):

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

        self.status(
            "● COPIED",
            ACCENT
        )

        self.root.after(
            1200,
            lambda: self.status(
                "● READY",
                ACCENT
            )
        )

    def copy_chat(self):

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
    # CHAT
    # ========================================================

    def new_chat(self):

        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        self.messages = []
        self.conversation = []

        self.add_message(
            "AI",
            "New conversation started."
        )

    def clear_chat(self):

        if not self.messages:
            return

        if messagebox.askyesno(
            "Clear",
            "Clear this conversation?"
        ):
            self.new_chat()

    # ========================================================
    # CHESS
    # ========================================================

    def open_chess(self):

        try:
            import chess
        except Exception:
            messagebox.showerror(
                "Chess",
                "Install python-chess first."
            )
            return

        window = tk.Toplevel(self.root)
        window.title("Autonomous AI — Chess")
        window.geometry("760x760")
        window.configure(bg=BG)

        tk.Label(
            window,
            text="♟  CHESS MODE",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(pady=15)

        board = chess.Board()

        canvas = tk.Canvas(
            window,
            width=640,
            height=640,
            highlightthickness=0
        )
        canvas.pack()

        selected = [None]

        piece_unicode = {
            "P":"♙","N":"♘","B":"♗","R":"♖","Q":"♕","K":"♔",
            "p":"♟","n":"♞","b":"♝","r":"♜","q":"♛","k":"♚"
        }

        def draw():

            canvas.delete("all")

            size = 80

            for row in range(8):

                for col in range(8):

                    light = (row + col) % 2 == 0

                    canvas.create_rectangle(
                        col*size,
                        row*size,
                        (col+1)*size,
                        (row+1)*size,
                        fill="#f0d9b5" if light else "#b58863",
                        outline=""
                    )

            for square in chess.SQUARES:

                piece = board.piece_at(square)

                if not piece:
                    continue

                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)

                canvas.create_text(
                    col*80+40,
                    row*80+40,
                    text=piece_unicode[piece.symbol()],
                    font=("Segoe UI Symbol", 44),
                    fill="#111111"
                )

            if selected[0] is not None:

                col = chess.square_file(selected[0])
                row = 7 - chess.square_rank(selected[0])

                canvas.create_rectangle(
                    col*80,
                    row*80,
                    (col+1)*80,
                    (row+1)*80,
                    outline=ACCENT,
                    width=4
                )

        def click(event):

            col = event.x // 80
            row = event.y // 80

            if not (0 <= col < 8 and 0 <= row < 8):
                return

            square = chess.square(
                col,
                7-row
            )

            if selected[0] is None:

                piece = board.piece_at(square)

                if piece and piece.color == board.turn:
                    selected[0] = square

            else:

                try:

                    move = chess.Move(
                        selected[0],
                        square
                    )

                    if move in board.legal_moves:
                        board.push(move)

                except Exception:
                    pass

                selected[0] = None

            draw()

        canvas.bind(
            "<Button-1>",
            click
        )

        draw()

    # ========================================================
    # VOICE PLACEHOLDER
    # ========================================================

    def record_audio(self):

        messagebox.showinfo(
            "Voice",
            "Voice input/output is kept separate from the Groq migration."
        )


def launch():

    root = tk.Tk()

    Dashboard(root)

    root.mainloop()


if __name__ == "__main__":
    launch()