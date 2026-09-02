import chess
import chess.engine
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ADAChess:

    def __init__(self):
        self.board = chess.Board()
        self.history = []

    def state(self):
        last = self.history[-1] if self.history else None

        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn else "black",
            "game_over": self.board.is_game_over(),
            "check": self.board.is_check(),
            "checkmate": self.board.is_checkmate(),
            "stalemate": self.board.is_stalemate(),
            "last_move": last,
            "history": self.history
        }

    def legal_moves(self):
        return [
            {
                "uci": m.uci(),
                "from": chess.square_name(m.from_square),
                "to": chess.square_name(m.to_square),
                "san": self.board.san(m)
            }
            for m in self.board.legal_moves
        ]

    def move(self, uci):
        move = chess.Move.from_uci(uci)

        if move not in self.board.legal_moves:
            raise ValueError("Illegal chess move.")

        item = {
            "uci": uci,
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "san": self.board.san(move)
        }

        self.board.push(move)
        self.history.append(item)

        return self.state()

    def restart(self):
        self.board.reset()
        self.history.clear()
        return self.state()

    def resign(self):
        return {
            "game_over": True,
            "reason": "resignation",
            "result": "0-1" if self.board.turn else "1-0"
        }

    def draw(self):
        return {
            "can_claim": self.board.can_claim_draw(),
            "threefold": self.board.can_claim_threefold_repetition(),
            "fifty_move": self.board.can_claim_fifty_moves(),
            "automatic": (
                self.board.is_stalemate()
                or self.board.is_insufficient_material()
                or self.board.is_seventyfive_moves()
                or self.board.is_fivefold_repetition()
            )
        }

    def analyze(self):
        candidates = [
            ROOT / "stockfish.exe",
            ROOT / "engines" / "stockfish.exe",
            ROOT / "bin" / "stockfish.exe"
        ]

        engine_path = None

        for candidate in candidates:
            if candidate.exists():
                engine_path = str(candidate)
                break

        if not engine_path:
            engine_path = shutil.which("stockfish")

        if not engine_path:
            return {
                "available": False,
                "message": "Stockfish is not installed."
            }

        engine = chess.engine.SimpleEngine.popen_uci(
            engine_path
        )

        try:
            info = engine.analyse(
                self.board,
                chess.engine.Limit(depth=12)
            )

            pv = info.get("pv", [])

            return {
                "available": True,
                "evaluation": str(
                    info["score"].pov(self.board.turn)
                ),
                "depth": info.get("depth"),
                "best_move": (
                    self.board.san(pv[0])
                    if pv else None
                ),
                "variation": [
                    self.board.san(m)
                    for m in pv[:8]
                ]
            }

        finally:
            engine.quit()


game = ADAChess()
