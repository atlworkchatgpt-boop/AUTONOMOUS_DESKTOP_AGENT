from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ada_chess import game


router = APIRouter(
    prefix="/api/chess",
    tags=["Chess"]
)


class MoveRequest(BaseModel):
    uci: str


@router.get("/state")
def chess_state():
    return game.state()


@router.get("/legal-moves")
def chess_legal_moves():
    return game.legal_moves()


@router.post("/move")
def chess_move(request: MoveRequest):
    try:
        return game.move(request.uci)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.post("/restart")
def chess_restart():
    return game.restart()


@router.post("/resign")
def chess_resign():
    return game.resign()


@router.post("/draw")
def chess_draw():
    return game.draw()


@router.post("/analysis")
def chess_analysis():
    return game.analyze()
