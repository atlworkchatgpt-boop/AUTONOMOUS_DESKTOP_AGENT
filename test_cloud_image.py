import os

from cloud_media import generate_image


if not os.environ.get("GEMINI_API_KEY"):
    print("GEMINI_API_KEY is not set.")
    print("Run SET_GEMINI_MEDIA_KEY.ps1 first.")
    raise SystemExit(1)

prompt = "A futuristic autonomous AI desktop assistant in a clean modern computer laboratory"

print("Generating image...")
result = generate_image(prompt)

print("")
print("SUCCESS")
print("File:", result["path"])
print("URL :", result["url"])
