import base64
import os
import tempfile
import uuid

from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from pydantic import BaseModel


router = APIRouter(
    prefix="/api/autonomous",
    tags=["autonomous-media"],
)


ROOT = (
    Path(__file__).resolve().parent.parent
)

OUTPUT = (
    ROOT
    /
    "web"
    /
    "static"
    /
    "generated"
)

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)


def key():

    value = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not value:

        raise HTTPException(
            status_code=503,
            detail=
                "GEMINI_API_KEY is not configured."
        )

    return value


class ImageRequest(BaseModel):

    prompt: str


@router.post("/image")
async def image(
    request: ImageRequest
):

    prompt = (
        request.prompt
        or
        ""
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Image prompt is empty."
        )

    try:

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=key()
        )

        response = (
            client.models.generate_content(
                model=
                    "gemini-3.1-flash-image",

                contents=
                    prompt,

                config=
                    types.GenerateContentConfig(
                        response_modalities=[
                            "TEXT",
                            "IMAGE"
                        ]
                    )
            )
        )

        image_bytes = None

        for candidate in (
            response.candidates or []
        ):

            content = getattr(
                candidate,
                "content",
                None
            )

            if not content:
                continue

            for part in (
                getattr(
                    content,
                    "parts",
                    []
                )
            ):

                inline_data = getattr(
                    part,
                    "inline_data",
                    None
                )

                if inline_data:

                    image_bytes = (
                        getattr(
                            inline_data,
                            "data",
                            None
                        )
                    )

                    if image_bytes:
                        break

            if image_bytes:
                break

        if not image_bytes:

            raise RuntimeError(
                "Gemini returned no image."
            )

        filename = (
            "image_"
            +
            uuid.uuid4().hex
            +
            ".png"
        )

        path = (
            OUTPUT
            /
            filename
        )

        path.write_bytes(
            bytes(image_bytes)
        )

        return {
            "ok":
                True,

            "url":
                "/static/generated/"
                +
                filename
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Image generation failed: "
                +
                str(exc)
        )


class VideoRequest(BaseModel):

    prompt: str


@router.post("/video")
async def video(
    request: VideoRequest
):

    prompt = (
        request.prompt
        or
        ""
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Video prompt is empty."
        )

    try:

        from google import genai

        client = genai.Client(
            api_key=key()
        )

        operation = client.models.generate_videos(
            model=
                "veo-3.1-generate-preview",

            prompt=
                prompt
        )

        operation_name = getattr(
            operation,
            "name",
            None
        )

        if not operation_name:

            raise RuntimeError(
                "Video operation name missing."
            )

        return {
            "ok":
                True,

            "operation_id":
                str(operation_name)
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Video generation failed: "
                +
                str(exc)
        )


@router.get(
    "/video/status/{operation_id:path}"
)
async def video_status(
    operation_id: str
):

    try:

        from google import genai

        client = genai.Client(
            api_key=key()
        )

        operation = client.operations.get(
            name=operation_id
        )

        if not getattr(
            operation,
            "done",
            False
        ):

            return {
                "status":
                    "processing"
            }

        error = getattr(
            operation,
            "error",
            None
        )

        if error:

            return {
                "status":
                    "failed",

                "error":
                    str(error)
            }

        response = getattr(
            operation,
            "response",
            None
        )

        url = None

        if response:

            videos = getattr(
                response,
                "generated_videos",
                None
            )

            if videos:

                video = getattr(
                    videos[0],
                    "video",
                    None
                )

                if video:

                    url = getattr(
                        video,
                        "uri",
                        None
                    )

        result = {
            "status":
                "completed"
        }

        if url:

            result["url"] = str(url)

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Video status failed: "
                +
                str(exc)
        )


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...)
):

    temporary = None

    try:

        from google import genai

        suffix = (
            Path(
                file.filename or
                "voice.webm"
            ).suffix
            or
            ".webm"
        )

        temporary = (
            Path(
                tempfile.gettempdir()
            )
            /
            (
                "autonomous_voice_"
                +
                uuid.uuid4().hex
                +
                suffix
            )
        )

        temporary.write_bytes(
            await file.read()
        )

        client = genai.Client(
            api_key=key()
        )

        uploaded = client.files.upload(
            file=str(temporary)
        )

        response = client.models.generate_content(
            model=
                "gemini-3.5-flash",

            contents=[
                "Transcribe this audio.",
                uploaded,
            ]
        )

        return {
            "text":
                (
                    getattr(
                        response,
                        "text",
                        ""
                    )
                    or
                    ""
                ).strip()
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=
                "Transcription failed: "
                +
                str(exc)
        )

    finally:

        if temporary:

            try:
                temporary.unlink(
                    missing_ok=True
                )
            except Exception:
                pass


