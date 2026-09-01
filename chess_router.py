from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chess_service import ChessGame

router = APIRouter(prefix="/api/chess", tags=["Chess"])

game = ChessGame()


class MoveRequest(BaseModel):
    uci: str


@router.get("/state")
def state():
    return game.state()


@router.get("/legal-moves")
def legal_moves():
    return game.legal_moves()


@router.post("/move")
def move(req: MoveRequest):
    try:
        return game.move(req.uci)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/restart")
def restart():
    return game.restart()


@router.post("/resign")
def resign():
    return game.resign()


@router.post("/draw")
def draw():
    return game.draw()


@router.post("/analysis")
def analysis():
    return game.analyze()
