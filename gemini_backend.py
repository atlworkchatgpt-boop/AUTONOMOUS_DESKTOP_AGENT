import os
import re

from google import genai
from google.genai import types


MODEL = "gemini-3.7-flash"


SYSTEM_PROMPT = """
You are Autonomous Desktop AI.

Creator:
Shreyansh Ray

You are a capable Windows desktop AI assistant.

Rules:

- Give accurate answers.
- Do not invent facts.
- When information may have changed recently, use Google Search
  grounding when available.
- Clearly distinguish verified current information from general knowledge.
- If current information cannot be verified, say so.
- Never claim to have performed a computer action unless it actually happened.
- Keep responses readable.
- Do not use unnecessary decorative asterisks.
- Use Markdown only when useful.
- For programming questions, give practical working solutions.
- Remember the current conversation.
"""


def create_client():

    key = os.environ.get(
        "GEMINI_API_KEY",
        ""
    ).strip()

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing."
        )

    return genai.Client(
        api_key=key
    )


def clean_text(text):

    if not text:
        return "Gemini returned an empty response."

    text = str(text)

    # Remove excessive decorative asterisks.
    text = re.sub(
        r"\*{3,}",
        "",
        text
    )

    text = re.sub(
        r"\n{4,}",
        "\n\n",
        text
    )

    return text.strip()


def ask(
    prompt,
    conversation=None
):

    client = create_client()

    conversation = conversation or []

    history = []

    for item in conversation:

        role = item.get("role")
        content = item.get(
            "content",
            ""
        )

        if role == "user":

            history.append(
                "USER:\n" + str(content)
            )

        elif role == "assistant":

            history.append(
                "ASSISTANT:\n" + str(content)
            )

    history_text = "\n\n".join(history)

    full_prompt = f"""
Previous conversation:

{history_text}

Current request:

{prompt}
"""

    # Google Search grounding.
    search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[
            search_tool
        ],
        thinking_config=types.ThinkingConfig(
            thinking_level="medium"
        )
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt,
        config=config
    )

    return clean_text(
        getattr(
            response,
            "text",
            ""
        )
    )


def test():

    print()
    print("=" * 60)
    print(" GEMINI BACKEND TEST")
    print("=" * 60)

    key = os.environ.get(
        "GEMINI_API_KEY",
        ""
    )

    print(
        "API KEY FOUND:",
        bool(key)
    )

    if key:
        print(
            "KEY LENGTH:",
            len(key)
        )

    print(
        "MODEL:",
        MODEL
    )

    print(
        "SEARCH GROUNDING: ENABLED"
    )

    print()

    try:

        answer = ask(
            "Say exactly: GEMINI BACKEND READY"
        )

        print("=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print()
        print(answer)

        return True

    except Exception as e:

        print("=" * 60)
        print("GEMINI REQUEST FAILED")
        print("=" * 60)
        print()
        print(
            type(e).__name__
        )
        print(
            str(e)
        )

        return False


if __name__ == "__main__":

    test()

    print()
    input(
        "Press Enter to close..."
    )
