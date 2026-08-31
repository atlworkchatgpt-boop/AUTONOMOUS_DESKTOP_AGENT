import random
import time
import uuid

import chess


LEVELS = {
    "Easy": (1, 0.05, 0.30),
    "Medium": (2, 0.12, 0.10),
    "Hard": (2, 0.25, 0.04),
    "Expert": (3, 0.45, 0.01),
    "Master": (3, 0.70, 0.00),
}


VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def evaluate(board):

    if board.is_checkmate():

        return (
            -1000000
            if board.turn == chess.WHITE
            else 1000000
        )

    if (
        board.is_stalemate()
        or
        board.is_insufficient_material()
    ):

        return 0

    score = 0

    for piece_type, value in VALUES.items():

        score += (
            len(
                board.pieces(
                    piece_type,
                    chess.WHITE
                )
            )
            * value
        )

        score -= (
            len(
                board.pieces(
                    piece_type,
                    chess.BLACK
                )
            )
            * value
        )

    for square in (
        chess.D4,
        chess.E4,
        chess.D5,
        chess.E5,
    ):

        piece = board.piece_at(square)

        if piece:

            score += (
                15
                if piece.color == chess.WHITE
                else -15
            )

    return score


def minimax(
    board,
    depth,
    alpha,
    beta,
    maximizing,
    deadline
):

    if time.monotonic() >= deadline:

        return evaluate(board), None

    if (
        depth <= 0
        or
        board.is_game_over()
    ):

        return evaluate(board), None

    moves = list(
        board.legal_moves
    )

    if not moves:

        return evaluate(board), None

    moves.sort(
        key=lambda move: (
            board.is_capture(move),
            board.gives_check(move)
        ),
        reverse=True
    )

    if maximizing:

        best_score = -10**9
        best_move = moves[0]

        for move in moves:

            if time.monotonic() >= deadline:
                break

            board.push(move)

            score, _ = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                False,
                deadline
            )

            board.pop()

            if score > best_score:

                best_score = score
                best_move = move

            alpha = max(
                alpha,
                best_score
            )

            if beta <= alpha:

                break

        return best_score, best_move

    best_score = 10**9
    best_move = moves[0]

    for move in moves:

        if time.monotonic() >= deadline:
            break

        board.push(move)

        score, _ = minimax(
            board,
            depth - 1,
            alpha,
            beta,
            True,
            deadline
        )

        board.pop()

        if score < best_score:

            best_score = score
            best_move = move

        beta = min(
            beta,
            best_score
        )

        if beta <= alpha:

            break

    return best_score, best_move


class Game:

    def __init__(
        self,
        color="white",
        difficulty="Medium"
    ):

        self.id = str(
            uuid.uuid4()
        )

        self.board = chess.Board()

        self.player_color = (
            chess.BLACK
            if str(color).lower()
            ==
            "black"
            else
            chess.WHITE
        )

        self.difficulty = (
            difficulty
            if difficulty in LEVELS
            else
            "Medium"
        )

    def move_ai(self):

        if self.board.is_game_over():

            return None

        depth, seconds, randomness = (
            LEVELS[
                self.difficulty
            ]
        )

        legal = list(
            self.board.legal_moves
        )

        if not legal:

            return None

        deadline = (
            time.monotonic()
            +
            seconds
        )

        maximizing = (
            self.board.turn
            ==
            chess.WHITE
        )

        _, move = minimax(
            self.board,
            depth,
            -10**9,
            10**9,
            maximizing,
            deadline
        )

        if move not in legal:

            move = random.choice(
                legal
            )

        if (
            randomness
            and
            random.random()
            <
            randomness
        ):

            move = random.choice(
                legal
            )

        self.board.push(
            move
        )

        return move

    def state(self):

        if self.board.is_checkmate():

            winner = (
                "Black"
                if self.board.turn
                ==
                chess.WHITE
                else
                "White"
            )

            return {
                "game_over":
                    True,

                "result":
                    winner
                    +
                    " wins by checkmate"
            }

        if self.board.is_stalemate():

            return {
                "game_over":
                    True,

                "result":
                    "Draw by stalemate"
            }

        if (
            self.board.is_insufficient_material()
        ):

            return {
                "game_over":
                    True,

                "result":
                    "Draw by insufficient material"
            }

        return {
            "game_over":
                False,

            "result":
                None
        }


GAMES = {}


def start(
    color="white",
    difficulty="Medium"
):

    game = Game(
        color,
        difficulty
    )

    GAMES[
        game.id
    ] = game

    return game


def get(game_id):

    game = GAMES.get(
        str(game_id)
    )

    if game is None:

        raise KeyError(
            "Game not found."
        )

    return game


def close(game_id):

    GAMES.pop(
        str(game_id),
        None
    )


def player_move(
    game_id,
    move_text
):

    game = get(
        game_id
    )

    if (
        game.board.turn
        !=
        game.player_color
    ):

        raise ValueError(
            "It is not your turn."
        )

    try:

        move = chess.Move.from_uci(
            str(move_text).strip()
        )

    except Exception:

        raise ValueError(
            "Invalid move."
        )

    if move not in game.board.legal_moves:

        raise ValueError(
            "Illegal move."
        )

    game.board.push(
        move
    )

    state = game.state()

    if state["game_over"]:

        return {
            "fen":
                game.board.fen(),

            "engine_move":
                None,

            "game_over":
                True,

            "result":
                state["result"]
        }

    engine_move = (
        game.move_ai()
    )

    state = game.state()

    return {
        "fen":
            game.board.fen(),

        "engine_move":
            (
                engine_move.uci()
                if engine_move
                else
                None
            ),

        "game_over":
            state["game_over"],

        "result":
            state["result"]
    }
