import os
import base64
import uuid
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent

IMAGE_DIR = ROOT / "data" / "generated" / "images"
VIDEO_DIR = ROOT / "data" / "generated" / "videos"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def image(prompt: str):

    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    model = os.getenv(
        "GEMINI_IMAGE_MODEL",
        "gemini-2.0-flash-exp"
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
        f"?key={key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": [
                "TEXT",
                "IMAGE"
            ]
        }
    }

    r = requests.post(
        url,
        json=payload,
        timeout=120
    )

    r.raise_for_status()

    data = r.json()

    for candidate in data.get("candidates", []):

        for part in candidate.get(
            "content", {}
        ).get("parts", []):

            inline = (
                part.get("inlineData")
                or part.get("inline_data")
            )

            if inline and inline.get("data"):

                raw = base64.b64decode(
                    inline["data"]
                )

                mime = inline.get(
                    "mimeType",
                    inline.get(
                        "mime_type",
                        "image/png"
                    )
                )

                ext = ".png"

                if "jpeg" in mime:
                    ext = ".jpg"

                name = (
                    "ada_"
                    + uuid.uuid4().hex
                    + ext
                )

                output = IMAGE_DIR / name
                output.write_bytes(raw)

                return {
                    "success": True,
                    "type": "image",
                    "url": (
                        f"/generated/images/{name}"
                    ),
                    "filename": name
                }

    raise RuntimeError(
        "No image was returned by the configured model."
    )


def video(prompt: str):

    # Kept as a clean cloud-video hook.
    # It does not falsely claim that a video was generated.
    return {
        "success": False,
        "type": "video",
        "status": "provider_required",
        "message": (
            "Configure a video-capable cloud provider "
            "for ADA video generation."
        )
    }
