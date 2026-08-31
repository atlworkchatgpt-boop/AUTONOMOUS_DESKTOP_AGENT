from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
)

from fastapi.responses import FileResponse

from pydantic import BaseModel

from web.isolated_media import (
    router as media_router
)

from web.isolated_chess import (
    start as chess_start_game,
    player_move as chess_player_move,
    close as chess_close_game,
    get as chess_get_game,
)

router = APIRouter()

router.include_router(
    media_router
)


# ---------------- CREATOR ----------------

@router.get(
    "/creator"
)
async def creator():

    path = (
        Path(__file__).resolve().parent
        /
        "static"
        /
        "creator.html"
    )

    if not path.is_file():

        raise HTTPException(
            status_code=404,
            detail="Creator page missing."
        )

    return FileResponse(
        str(path),
        media_type="text/html"
    )


# ---------------- CHESS ----------------

class ChessStart(BaseModel):

    color: str = "white"
    difficulty: str = "Medium"


class ChessMove(BaseModel):

    game_id: str
    move: str


class ChessClose(BaseModel):

    game_id: str


@router.post(
    "/api/autonomous/chess/start"
)
async def chess_start(
    request: ChessStart
):

    try:

        import chess

        game = chess_start_game(
            request.color,
            request.difficulty
        )

        if (
            game.player_color
            ==
            chess.BLACK
        ):

            game.engine_move()

        return {
            "game_id":
                game.game_id,

            "fen":
                game.board.fen(),

            "color":
                (
                    "black"
                    if game.player_color
                    ==
                    chess.BLACK
                    else
                    "white"
                ),

            "difficulty":
                game.difficulty
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Chess start failed: "
                +
                str(exc)
        )


@router.post(
    "/api/autonomous/chess/move"
)
async def chess_move(
    request: ChessMove
):

    try:

        return chess_player_move(
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


@router.post(
    "/api/autonomous/chess/close"
)
async def chess_close(
    request: ChessClose
):

    chess_close_game(
        request.game_id
    )

    return {
        "ok":
            True
    }


@router.get(
    "/api/autonomous/chess/test"
)
async def chess_test():

    game = chess_start_game(
        "white",
        "Easy"
    )

    try:

        result = chess_player_move(
            game.game_id,
            "e2e4"
        )

        return {
            "ok":
                True,

            "ai_move":
                result[
                    "engine_move"
                ],

            "fen":
                result[
                    "fen"
                ]
        }

    finally:

        chess_close_game(
            game.game_id
        )
