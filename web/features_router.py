import asyncio
from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
)

from fastapi.responses import FileResponse

from pydantic import BaseModel

from web.media import (
    router as media_router
)

router = APIRouter()

router.include_router(
    media_router
)


class SearchRequest(BaseModel):

    question: str


@router.post(
    "/api/live-search"
)
async def live_search(
    request: SearchRequest
):

    question = (
        request.question
        or
        ""
    ).strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question is empty."
        )

    try:

        from web.live_search import search

        return await asyncio.to_thread(
            search,
            question
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@router.get("/creator")
async def creator():

    path = (
        Path(__file__).resolve().parent
        /
        "static"
        /
        "creator.html"
    )

    return FileResponse(
        str(path),
        media_type="text/html"
    )


@router.get("/privacy")
async def privacy():

    path = (
        Path(__file__).resolve().parent
        /
        "static"
        /
        "privacy.html"
    )

    return FileResponse(
        str(path),
        media_type="text/html"
    )


@router.get("/terms")
async def terms():

    path = (
        Path(__file__).resolve().parent
        /
        "static"
        /
        "terms.html"
    )

    return FileResponse(
        str(path),
        media_type="text/html"
    )


class ChessStart(BaseModel):

    color: str = "white"
    difficulty: str = "Medium"


class ChessMove(BaseModel):

    game_id: str
    move: str


class ChessClose(BaseModel):

    game_id: str


@router.post(
    "/api/chess/start"
)
async def chess_start(
    request: ChessStart
):

    from web.chess_service import (
        start_game
    )

    try:

        game = start_game(
            request.color,
            request.difficulty
        )

        if (
            game.player_color
            == 
            __import__(
                "chess"
            ).BLACK
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
                    __import__(
                        "chess"
                    ).BLACK
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
                "Chess startup failed: "
                +
                str(exc)
        )


@router.post(
    "/api/chess/move"
)
async def chess_move(
    request: ChessMove
):

    from web.chess_service import (
        make_player_move
    )

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


@router.post(
    "/api/chess/close"
)
async def chess_close(
    request: ChessClose
):

    from web.chess_service import (
        remove_game
    )

    remove_game(
        request.game_id
    )

    return {
        "ok":
            True
    }


@router.get(
    "/api/chess/test"
)
async def chess_test():

    from web.chess_service import (
        start_game,
        make_player_move,
        remove_game
    )

    game = start_game(
        "white",
        "Easy"
    )

    try:

        result = make_player_move(
            game.game_id,
            "e2e4"
        )

        return {
            "ok":
                True,

            "ai_move":
                result["engine_move"],

            "fen":
                result["fen"]
        }

    finally:

        remove_game(
            game.game_id
        )
