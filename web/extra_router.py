from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from web.chess_service import (
    start_game,
    make_player_move,
    remove_game,
)


router = APIRouter()


# ============================================================
# CREATOR
# ============================================================

@router.get("/creator")
async def creator_page():

    from pathlib import Path

    path = (
        Path(__file__).resolve().parent
        /
        "static"
        /
        "creator.html"
    )

    if not path.is_file():

        raise HTTPException(
            status_code=500,
            detail="Creator page missing."
        )

    return FileResponse(
        str(path),
        media_type="text/html"
    )


# ============================================================
# CHESS API
# ============================================================

class ChessStart(BaseModel):

    color: str = "white"
    difficulty: str = "Medium"


class ChessMove(BaseModel):

    game_id: str
    move: str


class ChessClose(BaseModel):

    game_id: str


@router.post("/api/chess2/start")
async def chess_start(
    request: ChessStart
):

    try:

        game = start_game(
            request.color,
            request.difficulty
        )

        # Player is Black => AI opens as White.
        if game.player_color == __import__(
            "chess"
        ).BLACK:

            ai_move = game.ai_move()

        status = game.status()

        return {
            "game_id":
                game.game_id,

            "fen":
                game.board.fen(),

            "color":
                (
                    "black"
                    if game.player_color ==
                    __import__("chess").BLACK
                    else
                    "white"
                ),

            "difficulty":
                game.difficulty,

            "stockfish":
                False,

            "engine":
                "built-in",

            "game_over":
                status["game_over"],

            "result":
                status["result"],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Chess startup failed: "
                +
                str(exc)
            )
        )


@router.post("/api/chess2/move")
async def chess_move(
    request: ChessMove
):

    try:

        return make_player_move(
            request.game_id,
            request.move
        )

    except KeyError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Chess move failed: "
                +
                str(exc)
            )
        )


@router.post("/api/chess2/close")
async def chess_close(
    request: ChessClose
):

    remove_game(
        request.game_id
    )

    return {
        "ok": True
    }
