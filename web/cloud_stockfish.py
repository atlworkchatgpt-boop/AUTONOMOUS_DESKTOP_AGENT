from pathlib import Path
import os
import shutil


def find_stockfish():

    candidates = [
        os.getenv("STOCKFISH_PATH"),
        shutil.which("stockfish"),
        "/usr/games/stockfish",
        "/usr/bin/stockfish",
    ]

    for candidate in candidates:

        if not candidate:
            continue

        path = Path(candidate)

        if path.is_file():
            return str(path)

    return None
