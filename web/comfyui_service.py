from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests

try:
    import websocket
except Exception:
    websocket = None


COMFY_URL = os.getenv(
    "ADA_COMFY_URL",
    "http://127.0.0.1:8188"
).rstrip("/")

COMFY_DIR = Path(
    os.getenv(
        "ADA_COMFY_DIR",
        r"C:\Users\ADMIN\Desktop\ComfyUI-master\ComfyUI-master"
    )
)

OUTPUT_DIR = COMFY_DIR / "output"


def status() -> dict[str, Any]:

    try:
        r = requests.get(
            f"{COMFY_URL}/system_stats",
            timeout=5
        )

        if r.ok:
            return {
                "ok": True,
                "online": True,
                "url": COMFY_URL,
                "data": r.json()
            }

        return {
            "ok": False,
            "online": False,
            "url": COMFY_URL,
            "error": r.text
        }

    except Exception as e:

        return {
            "ok": False,
            "online": False,
            "url": COMFY_URL,
            "error": str(e)
        }


def get_object_info():

    r = requests.get(
        f"{COMFY_URL}/object_info",
        timeout=15
    )

    r.raise_for_status()

    return r.json()


def find_checkpoints():

    info = get_object_info()

    results = []

    try:
        files = info[
            "CheckpointLoaderSimple"
        ][
            "input"
        ][
            "required"
        ][
            "ckpt_name"
        ][0]

        if isinstance(files, list):
            results = files

    except Exception:
        pass

    return results


def _queue(prompt: dict, client_id: str):

    payload = {
        "prompt": prompt,
        "client_id": client_id
    }

    r = requests.post(
        f"{COMFY_URL}/prompt",
        json=payload,
        timeout=30
    )

    r.raise_for_status()

    return r.json()


def create_basic_image_workflow(
    prompt_text: str,
    negative_text: str = "",
    width: int = 512,
    height: int = 512,
    steps: int = 20,
    cfg: float = 7.0,
    seed: int | None = None
):

    checkpoints = find_checkpoints()

    if not checkpoints:
        raise RuntimeError(
            "No ComfyUI checkpoint was found. "
            "Put an image checkpoint in ComfyUI/models/checkpoints."
        )

    checkpoint = checkpoints[0]

    if seed is None:
        seed = int(time.time() * 1000) % 4294967295

    workflow = {

        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },

        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint
            }
        },

        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },

        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt_text,
                "clip": ["4", 1]
            }
        },

        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_text,
                "clip": ["4", 1]
            }
        },

        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },

        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "ADA",
                "images": ["8", 0]
            }
        }
    }

    return workflow


def generate_image(
    prompt_text: str,
    negative_text: str = "",
    width: int = 512,
    height: int = 512
):

    client_id = str(uuid.uuid4())

    workflow = create_basic_image_workflow(
        prompt_text,
        negative_text,
        width,
        height
    )

    result = _queue(
        workflow,
        client_id
    )

    prompt_id = result.get(
        "prompt_id"
    )

    if not prompt_id:
        raise RuntimeError(
            f"ComfyUI did not return prompt_id: {result}"
        )

    return {
        "ok": True,
        "type": "image",
        "prompt_id": prompt_id,
        "client_id": client_id,
        "message":
            "Image queued in ComfyUI."
    }


def find_video_workflows():

    candidates = []

    search_roots = [
        COMFY_DIR / "workflows",
        COMFY_DIR / "workflow",
        COMFY_DIR / "examples"
    ]

    for root in search_roots:

        if not root.exists():
            continue

        for p in root.rglob("*.json"):

            name = p.name.lower()

            if any(
                x in name
                for x in (
                    "video",
                    "wan",
                    "ltx",
                    "hunyuan",
                    "cosmos",
                    "animatediff"
                )
            ):
                candidates.append(p)

    return candidates


def generate_video(prompt_text: str):

    workflows = find_video_workflows()

    if not workflows:

        return {
            "ok": False,
            "type": "video",
            "error":
                "No ComfyUI video workflow was found. "
                "Install a video model/workflow in ComfyUI first."
        }

    workflow_file = workflows[0]

    try:

        workflow = json.loads(
            workflow_file.read_text(
                encoding="utf-8"
            )
        )

    except Exception as e:

        return {
            "ok": False,
            "type": "video",
            "error":
                f"Could not read workflow: {e}"
        }

    # Try to inject the requested prompt into
    # common text encoder nodes.

    changed = False

    for node in workflow.values():

        if not isinstance(node, dict):
            continue

        inputs = node.get(
            "inputs",
            {}
        )

        if not isinstance(inputs, dict):
            continue

        if "text" in inputs:

            current = str(
                inputs.get(
                    "text",
                    ""
                )
            )

            if current.strip():

                inputs["text"] = prompt_text
                changed = True

    if not changed:

        return {
            "ok": False,
            "type": "video",
            "error":
                "Video workflow was found, but no "
                "standard text prompt input could be detected.",
            "workflow":
                str(workflow_file)
        }

    client_id = str(uuid.uuid4())

    try:

        result = _queue(
            workflow,
            client_id
        )

        return {
            "ok": True,
            "type": "video",
            "prompt_id":
                result.get("prompt_id"),
            "workflow":
                str(workflow_file)
        }

    except Exception as e:

        return {
            "ok": False,
            "type": "video",
            "error": str(e)
        }


def history(prompt_id: str):

    r = requests.get(
        f"{COMFY_URL}/history/{prompt_id}",
        timeout=20
    )

    r.raise_for_status()

    return r.json()


def find_generated_files(prompt_id: str):

    data = history(prompt_id)

    entry = data.get(
        prompt_id
    )

    if not entry:
        return []

    outputs = entry.get(
        "outputs",
        {}
    )

    files = []

    for node_output in outputs.values():

        for key in (
            "images",
            "gifs",
            "videos"
        ):

            for item in node_output.get(
                key,
                []
            ):

                filename = item.get(
                    "filename"
                )

                subfolder = item.get(
                    "subfolder",
                    ""
                )

                if filename:

                    path = (
                        OUTPUT_DIR
                        / subfolder
                        / filename
                    )

                    files.append(
                        str(path)
                    )

    return files
