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
    prefix="/api/media",
    tags=["media"]
)

ROOT = (
    Path(__file__).resolve().parent.parent
)

GENERATED = (
    ROOT
    /
    "web"
    /
    "static"
    /
    "generated"
)

GENERATED.mkdir(
    parents=True,
    exist_ok=True
)


def get_key():

    key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not key:
        raise HTTPException(
            status_code=503,
            detail=
                "GEMINI_API_KEY is not configured."
        )

    return key


class ImageRequest(BaseModel):

    prompt: str


@router.post("/image")
async def image(
    request: ImageRequest
):

    prompt = str(
        request.prompt or ""
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
            api_key=get_key()
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[
                    "TEXT",
                    "IMAGE"
                ]
            )
        )

        image_data = None

        for candidate in response.candidates or []:

            content = getattr(
                candidate,
                "content",
                None
            )

            if not content:
                continue

            for part in getattr(
                content,
                "parts",
                []
            ):

                inline = getattr(
                    part,
                    "inline_data",
                    None
                )

                if inline:

                    image_data = getattr(
                        inline,
                        "data",
                        None
                    )

                    if image_data:
                        break

            if image_data:
                break

        if not image_data:

            raise RuntimeError(
                "No image returned by Gemini."
            )

        filename = (
            "generated_"
            +
            uuid.uuid4().hex
            +
            ".png"
        )

        path = (
            GENERATED /
            filename
        )

        if isinstance(
            image_data,
            str
        ):

            path.write_bytes(
                base64.b64decode(
                    image_data
                )
            )

        else:

            path.write_bytes(
                bytes(image_data)
            )

        return {
            "ok":
                True,

            "url":
                "/static/generated/"
                +
                filename,

            "filename":
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

    prompt = str(
        request.prompt or ""
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Video prompt is empty."
        )

    try:

        from google import genai

        client = genai.Client(
            api_key=get_key()
        )

        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt
        )

        operation_id = getattr(
            operation,
            "name",
            None
        )

        if not operation_id:

            operation_id = getattr(
                operation,
                "id",
                None
            )

        if not operation_id:

            raise RuntimeError(
                "Video operation ID was not returned."
            )

        return {
            "ok":
                True,

            "operation_id":
                str(operation_id)
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
            api_key=get_key()
        )

        operation = client.operations.get(
            name=operation_id
        )

        done = bool(
            getattr(
                operation,
                "done",
                False
            )
        )

        if not done:

            return {
                "status":
                    "processing"
            }

        result = getattr(
            operation,
            "response",
            None
        )

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

        video_url = None

        if result:

            generated_videos = getattr(
                result,
                "generated_videos",
                None
            )

            if generated_videos:

                first = (
                    generated_videos[0]
                )

                video = getattr(
                    first,
                    "video",
                    None
                )

                if video:

                    uri = getattr(
                        video,
                        "uri",
                        None
                    )

                    if uri:
                        video_url = str(uri)

        if video_url:

            return {
                "status":
                    "completed",

                "url":
                    video_url
            }

        return {
            "status":
                "completed"
        }

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
                file.filename or "voice.webm"
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
            api_key=get_key()
        )

        uploaded = client.files.upload(
            file=str(temporary)
        )

        response = client.models.generate_content(
            model="gemini-3.5-transcribe",
            contents=[
                uploaded
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
                "Voice transcription failed: "
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
