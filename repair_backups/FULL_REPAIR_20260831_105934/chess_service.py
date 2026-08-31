import random
import time
import uuid

import chess


LEVELS = {
    "Easy": (1, 0.10, 0.35),
    "Medium": (2, 0.20, 0.12),
    "Hard": (2, 0.35, 0.05),
    "Expert": (3, 0.55, 0.02),
    "Master": (3, 0.90, 0.00),
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

    if board.is_stalemate():
        return 0

    if board.is_insufficient_material():
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

    if depth <= 0 or board.is_game_over():
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


class ChessGame:

    def __init__(
        self,
        color="white",
        difficulty="Medium"
    ):

        self.game_id = str(
            uuid.uuid4()
        )

        self.board = chess.Board()

        self.player_color = (
            chess.BLACK
            if str(color).lower() == "black"
            else chess.WHITE
        )

        self.difficulty = (
            difficulty
            if difficulty in LEVELS
            else "Medium"
        )

    def status(self):

        if self.board.is_checkmate():

            winner = (
                "Black"
                if self.board.turn == chess.WHITE
                else "White"
            )

            return {
                "game_over": True,
                "result":
                    winner +
                    " wins by checkmate"
            }

        if self.board.is_stalemate():

            return {
                "game_over": True,
                "result":
                    "Draw by stalemate"
            }

        if self.board.is_insufficient_material():

            return {
                "game_over": True,
                "result":
                    "Draw by insufficient material"
            }

        if self.board.is_fivefold_repetition():

            return {
                "game_over": True,
                "result":
                    "Draw by repetition"
            }

        return {
            "game_over": False,
            "result": None
        }

    def engine_move(self):

        if self.board.is_game_over():
            return None

        depth, seconds, randomness = (
            LEVELS[
                self.difficulty
            ]
        )

        legal_moves = list(
            self.board.legal_moves
        )

        if not legal_moves:
            return None

        deadline = (
            time.monotonic()
            +
            seconds
        )

        maximizing = (
            self.board.turn ==
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

        if move not in legal_moves:
            move = random.choice(
                legal_moves
            )

        if (
            randomness > 0
            and
            random.random() < randomness
        ):

            move = random.choice(
                legal_moves
            )

        self.board.push(move)

        return move


GAMES = {}


def start_game(
    color="white",
    difficulty="Medium"
):

    game = ChessGame(
        color,
        difficulty
    )

    GAMES[
        game.game_id
    ] = game

    return game


def get_game(game_id):

    game = GAMES.get(
        str(game_id)
    )

    if game is None:
        raise KeyError(
            "Chess game not found."
        )

    return game


def remove_game(game_id):

    GAMES.pop(
        str(game_id),
        None
    )


def make_player_move(
    game_id,
    move_text
):

    game = get_game(
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
            "Invalid chess move."
        )

    if move not in game.board.legal_moves:

        raise ValueError(
            "Illegal chess move."
        )

    game.board.push(
        move
    )

    state = game.status()

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

    engine = game.engine_move()

    state = game.status()

    return {
        "fen":
            game.board.fen(),

        "engine_move":
            (
                engine.uci()
                if engine
                else None
            ),

        "game_over":
            state["game_over"],

        "result":
            state["result"]
    }
