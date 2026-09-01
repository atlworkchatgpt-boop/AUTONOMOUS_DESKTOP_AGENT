import chess
import chess.engine
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def find_stockfish():
    candidates = [
        ROOT / "stockfish.exe",
        ROOT / "engines" / "stockfish.exe",
        ROOT / "bin" / "stockfish.exe",
    ]

    for p in candidates:
        if p.exists():
            return str(p)

    return shutil.which("stockfish")


class ChessGame:

    def __init__(self):
        self.board = chess.Board()
        self.history = []

    def state(self):
        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn else "black",
            "legal_moves": self.legal_moves(),
            "history": self.history,
        }

    def legal_moves(self):
        return [
            {
                "uci": m.uci(),
                "from": chess.square_name(m.from_square),
                "to": chess.square_name(m.to_square),
                "san": self.board.san(m),
            }
            for m in self.board.legal_moves
        ]

    def move(self, uci):
        m = chess.Move.from_uci(uci)

        if m not in self.board.legal_moves:
            raise ValueError("Illegal move")

        san = self.board.san(m)

        data = {
            "uci": uci,
            "from": chess.square_name(m.from_square),
            "to": chess.square_name(m.to_square),
            "san": san,
        }

        self.board.push(m)
        self.history.append(data)

        return self.state()

    def restart(self):
        self.board.reset()
        self.history = []
        return self.state()

    def resign(self):
        return {
            "game_over": True,
            "reason": "resignation",
            "result": "0-1" if self.board.turn else "1-0",
        }

    def draw(self):
        return {
            "claimable": self.board.can_claim_draw(),
            "threefold": self.board.can_claim_threefold_repetition(),
            "fifty_move": self.board.can_claim_fifty_moves(),
            "automatic": (
                self.board.is_stalemate()
                or self.board.is_insufficient_material()
                or self.board.is_seventyfive_moves()
                or self.board.is_fivefold_repetition()
            ),
        }

    def analyze(self):
        path = find_stockfish()

        if not path:
            return {
                "available": False,
                "message": "Stockfish not found."
            }

        engine = chess.engine.SimpleEngine.popen_uci(path)

        try:
            info = engine.analyse(
                self.board,
                chess.engine.Limit(depth=12)
            )

            score = info["score"].pov(self.board.turn)

            pv = info.get("pv", [])

            return {
                "available": True,
                "evaluation": str(score),
                "depth": info.get("depth"),
                "best_move": (
                    self.board.san(pv[0])
                    if pv else None
                ),
                "variation": [
                    self.board.san(m)
                    for m in pv[:8]
                ],
            }

        finally:
            engine.quit()
