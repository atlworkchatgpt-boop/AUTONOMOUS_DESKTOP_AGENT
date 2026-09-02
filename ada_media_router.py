from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ada_media import image, video


router = APIRouter(
    prefix="/api/media",
    tags=["Media"]
)


class Prompt(BaseModel):
    prompt: str


@router.get("/status")
def status():

    import os

    return {
        "image": True,
        "video": True,
        "gemini_key_configured": bool(
            os.getenv("GEMINI_API_KEY")
        )
    }


@router.post("/image")
def create_image(request: Prompt):

    try:
        return image(request.prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@router.post("/video")
def create_video(request: Prompt):

    try:
        return video(request.prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
