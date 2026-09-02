from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cloud_media import generate_image, generate_video


router = APIRouter(
    prefix="/api/media",
    tags=["Cloud Media"]
)


class MediaRequest(BaseModel):
    prompt: str


@router.get("/status")
def media_status():
    import os

    return {
        "available": bool(os.environ.get("GEMINI_API_KEY")),
        "image_model": "gemini-3.1-flash-image",
        "video_model": "veo-3.1-generate-preview",
    }


@router.post("/image")
def media_image(request: MediaRequest):
    try:
        return generate_image(request.prompt)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {exc}"
        )


@router.post("/video")
def media_video(request: MediaRequest):
    try:
        return generate_video(request.prompt)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {exc}"
        )
