
from __future__ import annotations

import chess
import base64
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _gemini_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")




@router.get("/api/autonomous/status")
async def autonomous_status():
    configured = bool(_gemini_key())
    return {
        "ok": True,
        "creator": "Shreyansh Ray",
        "owner": "Shreyansh Ray",
        "guest_mode": True,
        "image_generation_configured": configured,
        "video_generation_configured": configured,
        "voice": True,
        "code_copy": True,
    }


class ImageRequest(BaseModel):
    prompt: str


@router.post("/api/autonomous/image")
async def generate_image(body: ImageRequest):
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Image prompt is empty.")

    key = _gemini_key()
    if not key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    try:
        from google import genai

        client = genai.Client(api_key=key)
        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=prompt,
        )

        output_image = getattr(interaction, "output_image", None)
        if not output_image or not getattr(output_image, "data", None):
            raise RuntimeError("Gemini did not return an image.")

        filename = f"image_{uuid.uuid4().hex}.png"
        destination = GENERATED_DIR / filename
        destination.write_bytes(base64.b64decode(output_image.data))

        return {
            "ok": True,
            "url": f"/static/generated/{filename}",
            "filename": filename,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}")


class VideoRequest(BaseModel):
    prompt: str


@router.post("/api/autonomous/video")
async def start_video(body: VideoRequest):
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Video prompt is empty.")

    key = _gemini_key()
    if not key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        response = client.videos.create(
            model="veo-3.1-generate-preview",
            prompt=prompt,
        )

        return {
            "ok": True,
            "operation_id": str(response.id),
            "status": str(getattr(response, "status", "processing")),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {exc}")


@router.get("/api/autonomous/video/status/{operation_id}")
async def video_status(operation_id: str):
    key = _gemini_key()
    if not key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        response = client.videos.retrieve(operation_id)

        status = str(getattr(response, "status", "processing"))
        result = {"status": status}

        if status == "completed":
            video = getattr(response, "video", None)
            url = getattr(video, "url", None) if video else None
            if url:
                result["url"] = str(url)

        error = getattr(response, "error", None)
        if error:
            result["error"] = str(error)

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video status failed: {exc}")


@router.post("/api/autonomous/transcribe")
async def transcribe(file: UploadFile = File(...)):
    key = _gemini_key()
    if not key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    suffix = Path(file.filename or "voice.webm").suffix or ".webm"
    temp = Path(tempfile.gettempdir()) / f"autonomous_voice_{uuid.uuid4().hex}{suffix}"

    try:
        temp.write_bytes(await file.read())

        from google import genai

        client = genai.Client(api_key=key)
        uploaded = client.files.upload(file=str(temp))
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=["Transcribe this audio exactly and return only the transcription.", uploaded],
        )

        return {"ok": True, "text": (getattr(response, "text", "") or "").strip()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
    finally:
        try:
            temp.unlink(missing_ok=True)
        except Exception:
            pass


# Compatibility aliases over the project's existing /api/chess/* service.
try:
    from web.chess_service import (
        make_player_move as _chess_move,
        remove_game as _chess_remove,
        start_game as _chess_start,
    )
except Exception:
    _chess_move = None
    _chess_remove = None
    _chess_start = None


class ChessStartRequest(BaseModel):
    color: str = "white"
    difficulty: str = "Medium"


class ChessMoveRequest(BaseModel):
    game_id: str
    move: str


class ChessCloseRequest(BaseModel):
    game_id: str


@router.post("/api/autonomous/chess/start")
async def chess_start(request: ChessStartRequest):
    if _chess_start is None:
        raise HTTPException(status_code=503, detail="Chess service unavailable.")
    try:
        game = _chess_start(request.color, request.difficulty)
        try:
            import chess
            if game.player_color == chess.BLACK:
                if hasattr(game, "engine_move"):
                    game.engine_move()
                elif hasattr(game, "ai_move"):
                    game.ai_move()
        except Exception:
            pass

        status = game.status() if hasattr(game, "status") else {}
        return {
            "game_id": game.game_id,
            "fen": game.board.fen(),
            "color": "black" if str(request.color).lower() == "black" else "white",
            "difficulty": getattr(game, "difficulty", request.difficulty),
            "game_over": bool(status.get("game_over", False)) if isinstance(status, dict) else False,
            "result": status.get("result") if isinstance(status, dict) else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chess start failed: {exc}")


@router.post("/api/autonomous/chess/move")
async def chess_move(request: ChessMoveRequest):
    if _chess_move is None:
        raise HTTPException(status_code=503, detail="Chess service unavailable.")
    try:
        return _chess_move(request.game_id, request.move)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chess move failed: {exc}")


@router.post("/api/autonomous/chess/close")
async def chess_close(request: ChessCloseRequest):
    if _chess_remove is not None:
        try:
            _chess_remove(request.game_id)
        except Exception:
            pass
    return {"ok": True}


@router.get("/api/autonomous/chess/test")
async def chess_test():
    if _chess_start is None or _chess_move is None:
        raise HTTPException(status_code=503, detail="Chess service unavailable.")

    game = None
    try:
        game = _chess_start("white", "Easy")
        result = _chess_move(game.game_id, "e2e4")
        return {
            "ok": True,
            "ai_move": result.get("engine_move"),
            "fen": result.get("fen"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chess test failed: {exc}")
    finally:
        if game is not None and _chess_remove is not None:
            try:
                _chess_remove(game.game_id)
            except Exception:
                pass


class ChessLegalMovesRequest(BaseModel):
    game_id: str
    square: str


@router.get("/api/autonomous/chess/legal-moves")
async def chess_legal_moves(
    game_id: str,
    square: str,
):
    try:
        import chess
        from web.chess_service import get_game

        game = get_game(game_id)

        square = str(square).strip().lower()

        try:
            from_square = chess.parse_square(square)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid chess square.",
            )

        # Only allow selecting a player's own piece.
        piece = game.board.piece_at(from_square)

        if piece is None:
            return {
                "game_id": game_id,
                "square": square,
                "legal_moves": [],
                "moves": [],
            }

        if piece.color != game.player_color:
            return {
                "game_id": game_id,
                "square": square,
                "legal_moves": [],
                "moves": [],
            }

        # If it is not the player's turn, don't expose moves
        # that cannot currently be played.
        if game.board.turn != game.player_color:
            return {
                "game_id": game_id,
                "square": square,
                "legal_moves": [],
                "moves": [],
            }

        legal = [
            move
            for move in game.board.legal_moves
            if move.from_square == from_square
        ]

        destinations = sorted(
            {
                chess.square_name(move.to_square)
                for move in legal
            }
        )

        return {
            "game_id": game_id,
            "square": square,
            "legal_moves": destinations,
            "moves": [
                {
                    "uci": move.uci(),
                    "from": chess.square_name(move.from_square),
                    "to": chess.square_name(move.to_square),
                }
                for move in legal
            ],
        }

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Chess game not found.",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Legal move calculation failed: {exc}",
        )

