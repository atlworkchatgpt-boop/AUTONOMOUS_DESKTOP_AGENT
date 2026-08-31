import os

# Gemini API key MUST be supplied as an environment variable.
# Never place the real key in GitHub source code.

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

def gemini_available():
    return bool(GEMINI_API_KEY)

def gemini_error_message(exc):
    text = str(exc)

    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        return (
            "Gemini generation is temporarily unavailable because "
            "the API quota/rate limit was exceeded. "
            "Check AI Studio usage/billing and try again later."
        )

    if "403" in text or "PERMISSION_DENIED" in text:
        return (
            "Gemini rejected the request. Check that the API key is "
            "valid, restricted correctly, and has Gemini API access."
        )

    return f"Gemini generation failed: {text}"
