import os
import time
import base64
from pathlib import Path

from google import genai

try:
    from google.genai import types
except Exception:
    types = None


ROOT = Path(__file__).resolve().parent

IMAGE_DIR = ROOT / "data" / "generated" / "images"
VIDEO_DIR = ROOT / "data" / "generated" / "videos"
WEB_DIR = ROOT / "web" / "static" / "generated"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set it in your environment before using media generation."
        )

    return key


def get_client():
    return genai.Client(api_key=get_api_key())


def generate_image(prompt: str):
    if not prompt or not prompt.strip():
        raise ValueError("Image prompt is empty.")

    client = get_client()

    response = client.interactions.create(
        model="gemini-3.1-flash-image",
        input=prompt,
        response_format={
            "type": "image",
            "aspect_ratio": "1:1",
            "image_size": "1K",
        },
    )

    image = getattr(response, "output_image", None)

    if image is None:
        raise RuntimeError(
            "Gemini returned no image. Check API access/quota/model availability."
        )

    data = base64.b64decode(image.data)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"ada_image_{timestamp}.png"

    local_path = IMAGE_DIR / filename
    web_path = WEB_DIR / filename

    local_path.write_bytes(data)
    web_path.write_bytes(data)

    return {
        "success": True,
        "type": "image",
        "filename": filename,
        "path": str(local_path),
        "url": f"/static/generated/{filename}",
    }


def generate_video(prompt: str):
    if not prompt or not prompt.strip():
        raise ValueError("Video prompt is empty.")

    client = get_client()

    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
    )

    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)

    if getattr(operation, "error", None):
        raise RuntimeError(str(operation.error))

    response = operation.response

    if not response or not response.generated_videos:
        raise RuntimeError(
            "Veo returned no video. Check API access/quota/model availability."
        )

    generated = response.generated_videos[0]

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"ada_video_{timestamp}.mp4"

    local_path = VIDEO_DIR / filename
    web_path = WEB_DIR / filename

    client.files.download(
        file=generated.video,
        destination=str(local_path),
    )

    web_path.write_bytes(local_path.read_bytes())

    return {
        "success": True,
        "type": "video",
        "filename": filename,
        "path": str(local_path),
        "url": f"/static/generated/{filename}",
    }
