import os
import shutil
import threading
import tkinter as tk
from tkinter import messagebox

import chess
import chess.engine


BG = "#181818"
TEXT = "#EEEEEE"
MUTED = "#999999"
ACCENT = "#10A37F"

LIGHT = "#F0D9B5"
DARK = "#B58863"
SELECT = "#10A37F"
LAST = "#D6C35A"


DIFFICULTIES = {
    "Easy": {
        "skill": 2,
        "time": 0.20,
        "depth": 8,
    },
    "Medium": {
        "skill": 7,
        "time": 0.50,
        "depth": 12,
    },
    "Hard": {
        "skill": 12,
        "time": 1.00,
        "depth": 16,
    },
    "Expert": {
        "skill": 17,
        "time": 2.00,
        "depth": 20,
    },
    "Master": {
        "skill": 20,
        "time": 4.00,
        "depth": 24,
    },
}


PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}


def find_stockfish():
    root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    candidates = [
        os.path.join(
            root,
            "stockfish.exe"
        ),
        shutil.which("stockfish"),
    ]

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


def launch(parent=None):

    window = (
        tk.Toplevel(parent)
        if parent is not None
        else tk.Tk()
    )

    window.title(
        "Autonomous AI - Stockfish Chess"
    )

    window.geometry(
        "900x950"
    )

    window.minsize(
        800,
        850
    )

    window.configure(
        bg=BG
    )

    board = chess.Board()

    state = {
        "player_color": chess.WHITE,
        "difficulty": "Medium",
        "engine": None,
        "engine_path": None,
        "selected": None,
        "last_move": None,
        "thinking": False,
        "closed": False,
    }

    # ========================================================
    # GAME FRAME
    # ========================================================

    chooser = tk.Frame(
        window,
        bg=BG
    )

    game = tk.Frame(
        window,
        bg=BG
    )

    # ========================================================
    # CHOOSE COLOR
    # ========================================================

    selected_color = tk.StringVar(
        value="White"
    )

    selected_difficulty = tk.StringVar(
        value="Medium"
    )

    tk.Label(
        chooser,
        text="CHESS MODE",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 28, "bold")
    ).pack(
        pady=(65, 8)
    )

    tk.Label(
        chooser,
        text="Choose your side",
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 11)
    ).pack(
        pady=(0, 14)
    )

    color_frame = tk.Frame(
        chooser,
        bg=BG
    )

    color_frame.pack(
        pady=5
    )

    tk.Radiobutton(
        color_frame,
        text="WHITE",
        variable=selected_color,
        value="White",
        bg=BG,
        fg=TEXT,
        selectcolor="#303030",
        activebackground=BG,
        activeforeground=TEXT,
        font=("Segoe UI", 11, "bold")
    ).pack(
        side="left",
        padx=28
    )

    tk.Radiobutton(
        color_frame,
        text="BLACK",
        variable=selected_color,
        value="Black",
        bg=BG,
        fg=TEXT,
        selectcolor="#303030",
        activebackground=BG,
        activeforeground=TEXT,
        font=("Segoe UI", 11, "bold")
    ).pack(
        side="left",
        padx=28
    )

    # ========================================================
    # DIFFICULTY
    # ========================================================

    tk.Label(
        chooser,
        text="Choose difficulty",
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 11)
    ).pack(
        pady=(35, 8)
    )

    difficulty_menu = tk.OptionMenu(
        chooser,
        selected_difficulty,
        *DIFFICULTIES.keys()
    )

    difficulty_menu.configure(
        bg="#303030",
        fg=TEXT,
        activebackground="#404040",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        width=18,
        font=("Segoe UI", 11)
    )

    difficulty_menu["menu"].configure(
        bg="#303030",
        fg=TEXT,
        activebackground=ACCENT,
        activeforeground="white"
    )

    difficulty_menu.pack(
        pady=(0, 8)
    )

    # Description changes with difficulty
    difficulty_description = tk.StringVar(
        value="Balanced Stockfish strength"
    )

    descriptions = {
        "Easy": "Fast and beginner-friendly",
        "Medium": "Balanced Stockfish strength",
        "Hard": "Strong tactical play",
        "Expert": "Very strong engine play",
        "Master": "Maximum configured strength",
    }

    def update_difficulty_description(*args):
        difficulty_description.set(
            descriptions.get(
                selected_difficulty.get(),
                ""
            )
        )

    selected_difficulty.trace_add(
        "write",
        update_difficulty_description
    )

    tk.Label(
        chooser,
        textvariable=difficulty_description,
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(
        pady=(0, 22)
    )

    sf_status = tk.StringVar(
        value="Checking Stockfish..."
    )

    tk.Label(
        chooser,
        textvariable=sf_status,
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(
        pady=8
    )

    # ========================================================
    # GAME HEADER
    # ========================================================

    player_text = tk.StringVar()
    difficulty_text = tk.StringVar()
    status = tk.StringVar()

    header = tk.Frame(
        game,
        bg=BG
    )

    header.pack(
        fill="x",
        pady=(15, 3)
    )

    tk.Label(
        header,
        text="STOCKFISH CHESS",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 21, "bold")
    ).pack(
        side="left",
        padx=22
    )

    tk.Label(
        header,
        textvariable=player_text,
        bg=BG,
        fg=ACCENT,
        font=("Segoe UI", 10, "bold")
    ).pack(
        side="right",
        padx=22
    )

    tk.Label(
        game,
        textvariable=difficulty_text,
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).pack()

    tk.Label(
        game,
        textvariable=status,
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 10, "bold")
    ).pack(
        pady=(5, 10)
    )

    # ========================================================
    # BOARD
    # ========================================================

    board_size = 680
    square = board_size // 8

    canvas = tk.Canvas(
        game,
        width=board_size,
        height=board_size,
        bg=LIGHT,
        highlightthickness=0
    )

    canvas.pack(
        padx=20
    )

    # ========================================================
    # STATUS
    # ========================================================

    def update_status():

        if board.is_checkmate():

            winner = (
                "BLACK"
                if board.turn == chess.WHITE
                else "WHITE"
            )

            status.set(
                "CHECKMATE - "
                + winner
                + " WINS"
            )

            return

        if board.is_stalemate():

            status.set(
                "DRAW - STALEMATE"
            )

            return

        if board.is_insufficient_material():

            status.set(
                "DRAW - INSUFFICIENT MATERIAL"
            )

            return

        if board.is_check():

            if board.turn == state["player_color"]:
                status.set("CHECK - YOUR MOVE")
            else:
                status.set("CHECK - STOCKFISH")

            return

        if board.turn == state["player_color"]:
            status.set("YOUR MOVE")
        else:
            status.set("STOCKFISH THINKING...")

    # ========================================================
    # DRAW
    # ========================================================

    def draw():

        canvas.delete("all")

        white_view = (
            state["player_color"] == chess.WHITE
        )

        for vr in range(8):

            for vc in range(8):

                if white_view:
                    file_index = vc
                    rank_index = 7 - vr
                else:
                    file_index = 7 - vc
                    rank_index = vr

                sq = chess.square(
                    file_index,
                    rank_index
                )

                x1 = vc * square
                y1 = vr * square
                x2 = x1 + square
                y2 = y1 + square

                fill = (
                    LIGHT
                    if (vr + vc) % 2 == 0
                    else DARK
                )

                if state["last_move"] and sq in (
                    state["last_move"].from_square,
                    state["last_move"].to_square
                ):
                    fill = LAST

                canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline=""
                )

                if state["selected"] == sq:

                    canvas.create_rectangle(
                        x1 + 3,
                        y1 + 3,
                        x2 - 3,
                        y2 - 3,
                        outline=SELECT,
                        width=5
                    )

                piece = board.piece_at(
                    sq
                )

                if piece:

                    canvas.create_text(
                        x1 + square / 2,
                        y1 + square / 2,
                        text=PIECES[
                            piece.symbol()
                        ],
                        font=(
                            "Segoe UI Symbol",
                            49
                        ),
                        fill="#111111"
                    )

        # Legal target markers
        if state["selected"] is not None:

            for move in board.legal_moves:

                if move.from_square != state["selected"]:
                    continue

                target = move.to_square

                if white_view:

                    vc = chess.square_file(target)
                    vr = 7 - chess.square_rank(target)

                else:

                    vc = 7 - chess.square_file(target)
                    vr = chess.square_rank(target)

                cx = (
                    vc * square
                    + square / 2
                )

                cy = (
                    vr * square
                    + square / 2
                )

                if board.piece_at(target):

                    canvas.create_oval(
                        cx - 20,
                        cy - 20,
                        cx + 20,
                        cy + 20,
                        outline=SELECT,
                        width=4
                    )

                else:

                    canvas.create_oval(
                        cx - 8,
                        cy - 8,
                        cx + 8,
                        cy + 8,
                        fill=SELECT,
                        outline=""
                    )

    # ========================================================
    # ENGINE MOVE
    # ========================================================

    def apply_engine_move(move):

        state["thinking"] = False

        if state["closed"]:
            return

        if move is None:
            update_status()
            draw()
            return

        if move not in board.legal_moves:

            messagebox.showerror(
                "Stockfish",
                "Engine produced an illegal move.",
                parent=window
            )

            return

        board.push(move)

        state["last_move"] = move
        state["selected"] = None

        draw()
        update_status()

    def engine_worker():

        if state["closed"]:
            return

        engine = state["engine"]

        if engine is None:
            return

        settings = DIFFICULTIES[
            state["difficulty"]
        ]

        try:
            engine.configure(
                {
                    "Skill Level": settings["skill"]
                }
            )
        except Exception:
            pass

        try:

            result = engine.play(
                board,
                chess.engine.Limit(
                    time=settings["time"],
                    depth=settings["depth"]
                )
            )

            move = result.move

        except Exception as exc:

            move = None

            if not state["closed"]:

                window.after(
                    0,
                    lambda err=str(exc):
                    messagebox.showerror(
                        "Stockfish",
                        err,
                        parent=window
                    )
                )

        if not state["closed"]:

            window.after(
                0,
                lambda m=move:
                apply_engine_move(m)
            )

    def engine_turn():

        if state["closed"]:
            return

        if board.is_game_over():
            return

        if board.turn == state["player_color"]:
            return

        state["thinking"] = True

        update_status()

        threading.Thread(
            target=engine_worker,
            daemon=True
        ).start()

    # ========================================================
    # BOARD CLICK
    # ========================================================

    def board_click(event):

        if state["thinking"]:
            return

        if board.is_game_over():
            return

        if board.turn != state["player_color"]:
            return

        vc = event.x // square
        vr = event.y // square

        if not (
            0 <= vc < 8
            and 0 <= vr < 8
        ):
            return

        white_view = (
            state["player_color"] == chess.WHITE
        )

        if white_view:

            file_index = vc
            rank_index = 7 - vr

        else:

            file_index = 7 - vc
            rank_index = vr

        target = chess.square(
            file_index,
            rank_index
        )

        if state["selected"] is None:

            piece = board.piece_at(
                target
            )

            if (
                piece
                and
                piece.color ==
                state["player_color"]
            ):

                state["selected"] = target
                draw()

            return

        if target == state["selected"]:

            state["selected"] = None
            draw()
            return

        move = chess.Move(
            state["selected"],
            target
        )

        piece = board.piece_at(
            state["selected"]
        )

        # Auto queen promotion
        if (
            piece
            and
            piece.piece_type == chess.PAWN
            and
            chess.square_rank(target) in (0, 7)
        ):

            move = chess.Move(
                state["selected"],
                target,
                promotion=chess.QUEEN
            )

        if move not in board.legal_moves:

            state["selected"] = None
            draw()
            status.set("ILLEGAL MOVE")
            return

        board.push(move)

        state["last_move"] = move
        state["selected"] = None

        draw()
        update_status()

        if not board.is_game_over():

            window.after(
                100,
                engine_turn
            )

    canvas.bind(
        "<Button-1>",
        board_click
    )

    # ========================================================
    # CLOSE
    # ========================================================

    def close_window():

        state["closed"] = True

        try:

            if state["engine"] is not None:
                state["engine"].quit()

        except Exception:
            pass

        window.destroy()

    # ========================================================
    # NEW GAME
    # ========================================================

    def new_game():

        board.reset()

        state["selected"] = None
        state["last_move"] = None
        state["thinking"] = False

        draw()
        update_status()

        if board.turn != state["player_color"]:

            window.after(
                300,
                engine_turn
            )

    # ========================================================
    # START GAME
    # ========================================================

    def start_game():

        engine_path = find_stockfish()

        if engine_path is None:

            messagebox.showerror(
                "Stockfish Not Found",
                (
                    "Stockfish was not found.\n\n"
                    "Expected location:\n\n"
                    + os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.abspath(__file__)
                            )
                        ),
                        "stockfish.exe"
                    )
                ),
                parent=window
            )

            return

        state["player_color"] = (
            chess.WHITE
            if selected_color.get() == "White"
            else
            chess.BLACK
        )

        state["difficulty"] = (
            selected_difficulty.get()
        )

        state["engine_path"] = engine_path

        try:

            state["engine"] = (
                chess.engine.SimpleEngine.popen_uci(
                    engine_path
                )
            )

            settings = DIFFICULTIES[
                state["difficulty"]
            ]

            try:

                state["engine"].configure(
                    {
                        "Skill Level":
                        settings["skill"]
                    }
                )

            except Exception:
                pass

        except Exception as exc:

            messagebox.showerror(
                "Stockfish Startup Failed",
                str(exc),
                parent=window
            )

            return

        chooser.pack_forget()

        game.pack(
            fill="both",
            expand=True
        )

        player_text.set(
            "YOU: "
            +
            (
                "WHITE"
                if state["player_color"] == chess.WHITE
                else
                "BLACK"
            )
        )

        difficulty_text.set(
            "DIFFICULTY: "
            + state["difficulty"]
        )

        board.reset()

        state["selected"] = None
        state["last_move"] = None

        draw()
        update_status()

        if state["player_color"] == chess.BLACK:

            window.after(
                300,
                engine_turn
            )

    # ========================================================
    # SETUP BUTTON
    # ========================================================

    tk.Button(
        chooser,
        text="START GAME",
        command=start_game,
        bg=ACCENT,
        fg="white",
        activebackground="#0D8E6F",
        relief="flat",
        bd=0,
        padx=45,
        pady=13,
        font=("Segoe UI", 11, "bold"),
        cursor="hand2"
    ).pack(
        pady=20
    )

    # ========================================================
    # GAME CONTROLS
    # ========================================================

    controls = tk.Frame(
        game,
        bg=BG
    )

    controls.pack(
        pady=16
    )

    tk.Button(
        controls,
        text="NEW GAME",
        command=new_game,
        bg=ACCENT,
        fg="white",
        activebackground="#0D8E6F",
        relief="flat",
        bd=0,
        padx=25,
        pady=10,
        cursor="hand2"
    ).pack(
        side="left",
        padx=5
    )

    tk.Button(
        controls,
        text="CLOSE",
        command=close_window,
        bg="#3A3A3A",
        fg=TEXT,
        activebackground="#4A4A4A",
        relief="flat",
        bd=0,
        padx=25,
        pady=10,
        cursor="hand2"
    ).pack(
        side="left",
        padx=5
    )

    window.protocol(
        "WM_DELETE_WINDOW",
        close_window
    )

    # ========================================================
    # STOCKFISH CHECK
    # ========================================================

    if find_stockfish():

        sf_status.set(
            "STOCKFISH READY"
        )

    else:

        sf_status.set(
            "STOCKFISH NOT FOUND"
        )

    chooser.pack(
        fill="both",
        expand=True
    )

    return window
