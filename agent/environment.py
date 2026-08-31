import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

# Load .env automatically for the dashboard/process.
load_dotenv(ROOT / ".env")

key = os.getenv("GROQ_API_KEY")

if not key:
    print("WARNING: GROQ_API_KEY is missing.")
else:
    print("GROQ_API_KEY: loaded")
