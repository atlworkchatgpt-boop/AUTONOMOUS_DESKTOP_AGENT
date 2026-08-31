import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_DIR = os.path.join(
    PROJECT_ROOT,
    "uploads"
)

RECORDING_DIR = os.path.join(
    PROJECT_ROOT,
    "recordings"
)

LOG_DIR = os.path.join(
    PROJECT_ROOT,
    "logs"
)

PASSWORD = "gngai"

# Fast models first.
MODEL_PREFERENCE = [
    "qwen2.5:1.5b-instruct-q4_0",
    "qwen2.5:1.5b",
    "qwen3:0.6b",
    "qwen2.5:0.5b-instruct",
    "qwen2.5:0.5b",
    "qwen2.5:7b"
]

for directory in [
    UPLOAD_DIR,
    RECORDING_DIR,
    LOG_DIR
]:
    os.makedirs(directory, exist_ok=True)

