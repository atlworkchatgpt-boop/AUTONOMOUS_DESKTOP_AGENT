import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import shutil

from agent.intelligence import Intelligence
from agent.config import UPLOAD_DIR


class Dashboard:

    def __init__(self, root):

        self.root = root
        self.root.title(
            "AUTONOMOUS DESKTOP AI"
        )

        self.root.geometry(
            "1200x760"
        )

        self.root.minsize(
            900,
            600
        )

        self.ai = Intelligence()

        self.busy = False

        self.build()

    # ========================================================
    # UI
    # ========================================================

    def build(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except Exception:
            pass

        main = ttk.Frame(
            self.root,
            padding=12
        )

        main.pack(
            fill="both",
            expand=True
        )

        # HEADER

        header = ttk.Frame(main)
        header.pack(
            fill="x",
            pady=(0, 10)
        )

        title = ttk.Label(
            header,
            text="AUTONOMOUS DESKTOP AI",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(
            side="left"
        )

        self.status = ttk.Label(
            header,
            text="● READY",
            font=("Segoe UI", 11, "bold")
        )

        self.status.pack(
            side="right"
        )

        # CHAT

        chat_frame = ttk.Frame(main)
        chat_frame.pack(
            fill="both",
            expand=True
        )

        self.chat = tk.Text(
            chat_frame,
            wrap="word",
            font=("Segoe UI", 11),
            state="disabled",
            padx=15,
            pady=15
        )

        scroll = ttk.Scrollbar(
            chat_frame,
            command=self.chat.yview
        )

        self.chat.configure(
            yscrollcommand=scroll.set
        )

        self.chat.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        # INPUT

        input_frame = ttk.Frame(main)
        input_frame.pack(
            fill="x",
            pady=10
        )

        self.entry = tk.Text(
            input_frame,
            height=4,
            font=("Segoe UI", 11)
        )

        self.entry.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.entry.bind(
            "<Control-Return>",
            lambda e: self.send()
        )

        buttons = ttk.Frame(
            input_frame
        )

        buttons.pack(
            side="right",
            fill="y",
            padx=(10, 0)
        )

        ttk.Button(
            buttons,
            text="SEND",
            command=self.send
        ).pack(
            fill="x",
            pady=2
        )

        ttk.Button(
            buttons,
            text="UPLOAD",
            command=self.upload
        ).pack(
            fill="x",
            pady=2
        )

        ttk.Button(
            buttons,
            text="COPY CHAT",
            command=self.copy_chat
        ).pack(
            fill="x",
            pady=2
        )

        ttk.Button(
            buttons,
            text="CLEAR",
            command=self.clear
        ).pack(
            fill="x",
            pady=2
        )

        # FOOTER

        footer = ttk.Label(
            main,
            text=(
                "Ctrl+Enter = Send   •   "
                "AI decides when to search or use tools   •   "
                "Protected actions require password"
            )
        )

        footer.pack(
            fill="x"
        )

        self.write(
            "SYSTEM",
            "Autonomous Desktop AI ready."
        )

    # ========================================================
    # CHAT
    # ========================================================

    def write(
        self,
        speaker,
        text
    ):

        self.chat.configure(
            state="normal"
        )

        self.chat.insert(
            "end",
            "\n"
            + speaker
            + "\n",
            "speaker"
        )

        self.chat.insert(
            "end",
            text
            + "\n"
        )

        self.chat.see(
            "end"
        )

        self.chat.configure(
            state="disabled"
        )

    # ========================================================
    # SEND
    # ========================================================

    def send(self):

        if self.busy:
            return

        message = self.entry.get(
            "1.0",
            "end"
        ).strip()

        if not message:
            return

        self.entry.delete(
            "1.0",
            "end"
        )

        self.write(
            "YOU",
            message
        )

        self.busy = True

        self.status.configure(
            text="● THINKING..."
        )

        threading.Thread(
            target=self.worker,
            args=(message,),
            daemon=True
        ).start()

    def worker(self, message):

        try:

            answer = self.ai.respond(
                message
            )

        except Exception as e:

            answer = (
                "AI engine error:\n"
                + str(e)
            )

        self.root.after(
            0,
            lambda:
                self.finish(answer)
        )

    def finish(self, answer):

        self.write(
            "AI",
            answer
        )

        self.busy = False

        self.status.configure(
            text="● READY"
        )

    # ========================================================
    # UPLOAD
    # ========================================================

    def upload(self):

        paths = filedialog.askopenfilenames(
            title="Select files"
        )

        if not paths:
            return

        copied = []

        for path in paths:

            try:

                destination = os.path.join(
                    UPLOAD_DIR,
                    os.path.basename(path)
                )

                shutil.copy2(
                    path,
                    destination
                )

                copied.append(
                    destination
                )

            except Exception as e:

                self.write(
                    "SYSTEM",
                    "Upload failed: "
                    + str(e)
                )

        if copied:

            self.write(
                "SYSTEM",
                "Uploaded:\n"
                + "\n".join(copied)
            )

            self.entry.insert(
                "end",
                "I uploaded these files. Analyze them if relevant."
            )

    # ========================================================
    # COPY
    # ========================================================

    def copy_chat(self):

        text = self.chat.get(
            "1.0",
            "end"
        )

        self.root.clipboard_clear()

        self.root.clipboard_append(
            text
        )

        self.status.configure(
            text="● COPIED"
        )

        self.root.after(
            1200,
            lambda:
                self.status.configure(
                    text="● READY"
                )
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self):

        if messagebox.askyesno(
            "Clear chat",
            "Clear the visible conversation?"
        ):

            self.chat.configure(
                state="normal"
            )

            self.chat.delete(
                "1.0",
                "end"
            )

            self.chat.configure(
                state="disabled"
            )


def launch():

    root = tk.Tk()

    Dashboard(root)

    root.mainloop()


if __name__ == "__main__":
    launch()
