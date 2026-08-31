import threading
import tkinter as tk

import chess


class ChessAI:

    VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    # Simple piece-square bonuses.
    PAWN_TABLE = [
         0,  5,  5,  0,  5,  10,  50,  0,
         0,  10, -5,  0,  5,  10,  50,  0,
         0,  10, -10, 0, 10, 20,  50,  0,
         0, -20,  0, 20, 25, 30,  0,   0,
         0, -20,  0, 20, 25, 30,  0,   0,
         0,  10, -10, 0, 10, 20,  50,  0,
         0,  10, -5, 0, 5, 10,  50,   0,
         0,  5,  5, 0, 5, 10,  50,   0,
    ]

    def __init__(
        self,
        depth=2,
    ):

        self.depth = depth

    def evaluate(
        self,
        board,
    ):

        if board.is_checkmate():

            if board.turn == chess.WHITE:
                return -100000
            return 100000

        if board.is_stalemate():
            return 0

        score = 0

        for square, piece in board.piece_map().items():

            value = self.VALUES[
                piece.piece_type
            ]

            if piece.piece_type == chess.PAWN:

                rank = chess.square_rank(
                    square
                )

                if piece.color == chess.BLACK:
                    rank = 7 - rank

                value += self.PAWN_TABLE[
                    rank * 8
                    + chess.square_file(square)
                ]

            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value

        # Small positional bonuses.
        score += (
            8
            * (
                len(
                    board.attackers(
                        chess.WHITE,
                        chess.E4
                    )
                )
                -
                len(
                    board.attackers(
                        chess.BLACK,
                        chess.E5
                    )
                )
            )
        )

        return score

    def choose_move(
        self,
        board,
    ):

        maximizing = (
            board.turn == chess.WHITE
        )

        best_move = None

        if maximizing:
            best_score = -10**9
        else:
            best_score = 10**9

        moves = list(
            board.legal_moves
        )

        # Prefer captures/checks during move ordering.
        moves.sort(
            key=lambda move: (
                board.is_capture(move),
                board.gives_check(move),
                move.to_square,
            ),
            reverse=True,
        )

        for move in moves:

            board.push(
                move
            )

            score = self.minimax(
                board,
                self.depth - 1,
                -10**9,
                10**9,
            )

            board.pop()

            if maximizing:

                if score > best_score:

                    best_score = score
                    best_move = move

            else:

                if score < best_score:

                    best_score = score
                    best_move = move

        return best_move

    def minimax(
        self,
        board,
        depth,
        alpha,
        beta,
    ):

        if depth <= 0:
            return self.evaluate(board)

        if board.is_game_over(
            claim_draw=True
        ):

            return self.evaluate(
                board
            )

        maximizing = (
            board.turn == chess.WHITE
        )

        moves = list(
            board.legal_moves
        )

        moves.sort(
            key=lambda move: (
                board.is_capture(move),
                board.gives_check(move),
            ),
            reverse=True,
        )

        if maximizing:

            value = -10**9

            for move in moves:

                board.push(move)

                value = max(
                    value,
                    self.minimax(
                        board,
                        depth - 1,
                        alpha,
                        beta,
                    ),
                )

                board.pop()

                alpha = max(
                    alpha,
                    value
                )

                if alpha >= beta:
                    break

            return value

        value = 10**9

        for move in moves:

            board.push(move)

            value = min(
                value,
                self.minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                ),
            )

            board.pop()

            beta = min(
                beta,
                value
            )

            if alpha >= beta:
                break

        return value


class ChessWindow:

    LIGHT = "#f0d9b5"
    DARK = "#b58863"
    HIGHLIGHT = "#f6f669"
    LAST_MOVE = "#cdd26a"

    def __init__(
        self,
        parent,
    ):

        self.parent = parent

        self.window = tk.Toplevel(
            parent
        )

        self.window.title(
            "Autonomous Chess"
        )

        self.window.geometry(
            "760x730"
        )

        self.window.minsize(
            680,
            650
        )

        self.window.configure(
            bg="#171717"
        )

        self.board = chess.Board()

        # User is White.
        self.human_color = chess.WHITE

        self.ai_color = chess.BLACK

        self.ai = ChessAI(
            depth=2
        )

        self.selected_square = None

        self.last_move = None

        self.ai_thinking = False

        self.status = tk.StringVar(
            value="Your move — White"
        )

        self._build()

        self.draw_board()

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

    # ========================================================
    # UI
    # ========================================================

    def _build(self):

        header = tk.Frame(
            self.window,
            bg="#171717"
        )

        header.pack(
            fill="x",
            padx=20,
            pady=15
        )

        tk.Label(
            header,
            text="\u265F  AUTONOMOUS CHESS",
            bg="#171717",
            fg="#ffffff",
            font=(
                "Segoe UI",
                16,
                "bold"
            )
        ).pack(
            side="left"
        )

        tk.Label(
            header,
            textvariable=self.status,
            bg="#171717",
            fg="#10a37f",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="right"
        )

        self.canvas = tk.Canvas(
            self.window,
            width=640,
            height=640,
            bg="#111111",
            highlightthickness=0
        )

        self.canvas.pack(
            padx=20,
            pady=5
        )

        controls = tk.Frame(
            self.window,
            bg="#171717"
        )

        controls.pack(
            fill="x",
            padx=20,
            pady=12
        )

        tk.Button(
            controls,
            text="\U0001F504 New Game",
            command=self.new_game,
            bg="#2f2f2f",
            fg="#ffffff",
            activebackground="#444444",
            relief="flat",
            bd=0,
            padx=18,
            pady=9
        ).pack(
            side="left"
        )

        tk.Button(
            controls,
            text="\U0001F9E0 AI Move",
            command=self.force_ai_move,
            bg="#10a37f",
            fg="#ffffff",
            activebackground="#0d8f70",
            relief="flat",
            bd=0,
            padx=18,
            pady=9
        ).pack(
            side="right"
        )

        self.canvas.bind(
            "<Button-1>",
            self.click_board
        )

    # ========================================================
    # DRAW BOARD
    # ========================================================

    def draw_board(self):

        self.canvas.delete(
            "all"
        )

        size = 640
        square = size // 8

        for rank in range(8):

            for file_index in range(8):

                x1 = (
                    file_index
                    * square
                )

                y1 = (
                    rank
                    * square
                )

                x2 = x1 + square
                y2 = y1 + square

                color = (
                    self.LIGHT
                    if (
                        rank + file_index
                    ) % 2 == 0
                    else self.DARK
                )

                square_index = chess.square(
                    file_index,
                    7 - rank
                )

                if (
                    self.selected_square
                    == square_index
                ):

                    color = self.HIGHLIGHT

                elif (
                    self.last_move
                    and square_index
                    in (
                        self.last_move.from_square,
                        self.last_move.to_square,
                    )
                ):

                    color = self.LAST_MOVE

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=""
                )

                # Coordinate labels.
                if rank == 7:

                    self.canvas.create_text(
                        x2 - 8,
                        y2 - 8,
                        text=chr(
                            97 + file_index
                        ),
                        fill=(
                            self.DARK
                            if (
                                rank
                                + file_index
                            ) % 2 == 0
                            else self.LIGHT
                        ),
                        font=(
                            "Segoe UI",
                            8,
                            "bold"
                        )
                    )

                if file_index == 0:

                    self.canvas.create_text(
                        x1 + 8,
                        y1 + 9,
                        text=str(
                            8 - rank
                        ),
                        fill=(
                            self.DARK
                            if (
                                rank
                                + file_index
                            ) % 2 == 0
                            else self.LIGHT
                        ),
                        font=(
                            "Segoe UI",
                            8,
                            "bold"
                        )
                    )

        self.draw_pieces()

    # ========================================================
    # DRAW REAL-LOOKING PIECES WITH CANVAS SHAPES
    # ========================================================

    def draw_pieces(self):

        square = 80

        for square_index, piece in (
            self.board.piece_map().items()
        ):

            file_index = chess.square_file(
                square_index
            )

            rank = 7 - chess.square_rank(
                square_index
            )

            cx = (
                file_index
                * square
                + square / 2
            )

            cy = (
                rank
                * square
                + square / 2
            )

            self.draw_piece(
                cx,
                cy,
                piece,
                square,
            )

    def draw_piece(
        self,
        cx,
        cy,
        piece,
        size,
    ):

        # Canvas vector pieces.
        # No Unicode character is used for the actual piece.

        fill = (
            "#f7f7f7"
            if piece.color == chess.WHITE
            else "#202020"
        )

        outline = (
            "#242424"
            if piece.color == chess.WHITE
            else "#d0d0d0"
        )

        p = size

        # Base.
        self.canvas.create_oval(
            cx - p * 0.25,
            cy + p * 0.26,
            cx + p * 0.25,
            cy + p * 0.38,
            fill=fill,
            outline=outline,
            width=2,
        )

        self.canvas.create_rectangle(
            cx - p * 0.20,
            cy + p * 0.18,
            cx + p * 0.20,
            cy + p * 0.31,
            fill=fill,
            outline=outline,
            width=2,
        )

        # Body.
        body_top = cy - p * 0.05
        body_bottom = cy + p * 0.20

        self.canvas.create_polygon(
            cx - p * 0.17,
            body_bottom,
            cx - p * 0.13,
            body_top,
            cx + p * 0.13,
            body_top,
            cx + p * 0.17,
            body_bottom,
            fill=fill,
            outline=outline,
            width=2,
        )

        # Different silhouettes.
        if piece.piece_type == chess.PAWN:

            self.canvas.create_oval(
                cx - p * 0.12,
                cy - p * 0.23,
                cx + p * 0.12,
                cy - p * 0.01,
                fill=fill,
                outline=outline,
                width=2,
            )

            self.canvas.create_oval(
                cx - p * 0.08,
                cy - p * 0.35,
                cx + p * 0.08,
                cy - p * 0.19,
                fill=fill,
                outline=outline,
                width=2,
            )

        elif piece.piece_type == chess.KING:

            self.canvas.create_rectangle(
                cx - p * 0.04,
                cy - p * 0.30,
                cx + p * 0.04,
                cy - p * 0.05,
                fill=fill,
                outline=outline,
                width=2,
            )

            self.canvas.create_rectangle(
                cx - p * 0.11,
                cy - p * 0.22,
                cx + p * 0.11,
                cy - p * 0.14,
                fill=fill,
                outline=outline,
                width=2,
            )

            self.canvas.create_polygon(
                cx - p * 0.14,
                cy - p * 0.33,
                cx,
                cy - p * 0.48,
                cx + p * 0.14,
                cy - p * 0.33,
                fill=fill,
                outline=outline,
                width=2,
            )

        elif piece.piece_type == chess.QUEEN:

            self.canvas.create_polygon(
                cx - p * 0.18,
                cy - p * 0.06,
                cx - p * 0.14,
                cy - p * 0.30,
                cx - p * 0.07,
                cy - p * 0.19,
                cx,
                cy - p * 0.34,
                cx + p * 0.07,
                cy - p * 0.19,
                cx + p * 0.14,
                cy - p * 0.30,
                cx + p * 0.18,
                cy - p * 0.06,
                fill=fill,
                outline=outline,
                width=2,
            )

        elif piece.piece_type == chess.ROOK:

            self.canvas.create_rectangle(
                cx - p * 0.14,
                cy - p * 0.34,
                cx + p * 0.14,
                cy - p * 0.06,
                fill=fill,
                outline=outline,
                width=2,
            )

            for offset in (
                -0.11,
                0,
                0.11,
            ):

                self.canvas.create_rectangle(
                    cx
                    + p * offset
                    - p * 0.035,
                    cy - p * 0.43,
                    cx
                    + p * offset
                    + p * 0.035,
                    cy - p * 0.30,
                    fill=fill,
                    outline=outline,
                    width=1,
                )

        elif piece.piece_type == chess.BISHOP:

            self.canvas.create_oval(
                cx - p * 0.13,
                cy - p * 0.40,
                cx + p * 0.13,
                cy - p * 0.10,
                fill=fill,
                outline=outline,
                width=2,
            )

            self.canvas.create_line(
                cx,
                cy - p * 0.37,
                cx + p * 0.05,
                cy - p * 0.15,
                fill=outline,
                width=2,
            )

        elif piece.piece_type == chess.KNIGHT:

            self.canvas.create_polygon(
                cx - p * 0.16,
                cy + p * 0.03,
                cx - p * 0.18,
                cy - p * 0.23,
                cx - p * 0.04,
                cy - p * 0.43,
                cx + p * 0.14,
                cy - p * 0.34,
                cx + p * 0.08,
                cy - p * 0.12,
                cx + p * 0.18,
                cy + p * 0.05,
                fill=fill,
                outline=outline,
                width=2,
            )

        # Small center highlight.
        self.canvas.create_oval(
            cx - p * 0.025,
            cy - p * 0.08,
            cx + p * 0.025,
            cy - p * 0.03,
            fill=outline,
            outline=""
        )

    # ========================================================
    # PLAYER INPUT
    # ========================================================

    def click_board(
        self,
        event,
    ):

        if self.ai_thinking:
            return

        if self.board.turn != self.human_color:
            return

        file_index = max(
            0,
            min(
                7,
                event.x // 80
            )
        )

        rank = 7 - max(
            0,
            min(
                7,
                event.y // 80
            )
        )

        square = chess.square(
            file_index,
            rank
        )

        piece = self.board.piece_at(
            square
        )

        # Select own piece.
        if self.selected_square is None:

            if (
                piece
                and piece.color
                == self.human_color
            ):

                self.selected_square = square

                self.status.set(
                    "Choose destination"
                )

                self.draw_board()

            return

        # Click same square = deselect.
        if square == self.selected_square:

            self.selected_square = None

            self.status.set(
                "Your move — White"
            )

            self.draw_board()

            return

        move = chess.Move(
            self.selected_square,
            square
        )

        # Automatic promotion to queen.
        moving_piece = self.board.piece_at(
            self.selected_square
        )

        if (
            moving_piece
            and moving_piece.piece_type
            == chess.PAWN
            and chess.square_rank(square)
            in (
                0,
                7
            )
        ):

            move = chess.Move(
                self.selected_square,
                square,
                promotion=chess.QUEEN
            )

        if move not in self.board.legal_moves:

            self.status.set(
                "Illegal move"
            )

            return

        self.board.push(
            move
        )

        self.last_move = move

        self.selected_square = None

        self.draw_board()

        if self.board.is_game_over(
            claim_draw=True
        ):

            self.show_game_over()

            return

        self.status.set(
            "AI thinking..."
        )

        self.start_ai_move()

    # ========================================================
    # AI
    # ========================================================

    def start_ai_move(self):

        if self.ai_thinking:
            return

        self.ai_thinking = True

        threading.Thread(
            target=self._ai_worker,
            daemon=True
        ).start()

    def _ai_worker(self):

        try:

            move = self.ai.choose_move(
                self.board.copy()
            )

        except Exception as exc:

            self.root_safe(
                lambda: self.ai_error(
                    exc
                )
            )

            return

        self.root_safe(
            lambda: self.finish_ai_move(
                move
            )
        )

    def finish_ai_move(
        self,
        move
    ):

        self.ai_thinking = False

        if move is None:

            self.show_game_over()

            return

        if move not in self.board.legal_moves:

            self.status.set(
                "AI produced an illegal move."
            )

            return

        self.board.push(
            move
        )

        self.last_move = move

        self.draw_board()

        if self.board.is_game_over(
            claim_draw=True
        ):

            self.show_game_over()

        else:

            self.status.set(
                "Your move — White"
            )

    def force_ai_move(self):

        if self.board.turn == self.ai_color:

            self.start_ai_move()

    # ========================================================
    # NEW GAME
    # ========================================================

    def new_game(self):

        self.board.reset()

        self.selected_square = None

        self.last_move = None

        self.ai_thinking = False

        self.status.set(
            "Your move — White"
        )

        self.draw_board()

    # ========================================================
    # GAME OVER
    # ========================================================

    def show_game_over(self):

        if self.board.is_checkmate():

            winner = (
                "Black"
                if self.board.turn
                == chess.WHITE
                else "White"
            )

            self.status.set(
                f"Checkmate — {winner} wins"
            )

        elif self.board.is_stalemate():

            self.status.set(
                "Draw — stalemate"
            )

        elif self.board.is_insufficient_material():

            self.status.set(
                "Draw — insufficient material"
            )

        else:

            self.status.set(
                "Game over"
            )

    def ai_error(
        self,
        exc
    ):

        self.ai_thinking = False

        self.status.set(
            "AI error"
        )

        messagebox = tk.Toplevel(
            self.window
        )

        messagebox.title(
            "Chess AI Error"
        )

        tk.Label(
            messagebox,
            text=str(exc),
            bg="#202020",
            fg="#ffffff",
            wraplength=400,
            padx=20,
            pady=20
        ).pack()

        tk.Button(
            messagebox,
            text="OK",
            command=messagebox.destroy
        ).pack(
            pady=(0, 15)
        )

    # ========================================================
    # SAFE TK CALL
    # ========================================================

    def root_safe(
        self,
        callback
    ):

        try:

            self.window.after(
                0,
                callback
            )

        except Exception:

            pass

    def close(self):

        try:
            self.window.destroy()
        except Exception:
            pass


# Compatibility alias.
ChessMode = ChessWindow