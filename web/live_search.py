import os


def needs_live_search(question):

    q = str(
        question or ""
    ).lower()

    terms = (
        "today",
        "latest",
        "current",
        "right now",
        "recent",
        "news",
        "who won",
        "who is the current",
        "score",
        "scores",
        "result",
        "results",
        "fifa",
        "world cup",
        "election",
        "president",
        "prime minister",
        "weather",
        "price",
        "stock",
        "2026",
        "2025",
        "this week",
        "this month",
        "this year",
    )

    return any(
        term in q
        for term in terms
    )


def search(question):

    key = (
        os.getenv("GEMINI_API_KEY")
        or
        os.getenv("GOOGLE_API_KEY")
    )

    if not key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=key
    )

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=str(question),
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ]
        )
    )

    answer = (
        getattr(
            response,
            "text",
            ""
        )
        or
        ""
    ).strip()

    sources = []

    grounding = getattr(
        response,
        "grounding_metadata",
        None
    )

    if grounding:

        chunks = getattr(
            grounding,
            "grounding_chunks",
            None
        )

        if chunks:

            seen = set()

            for chunk in chunks:

                web = getattr(
                    chunk,
                    "web",
                    None
                )

                if not web:
                    continue

                url = getattr(
                    web,
                    "uri",
                    None
                )

                if not url:
                    continue

                url = str(url)

                if url in seen:
                    continue

                seen.add(url)

                title = getattr(
                    web,
                    "title",
                    None
                ) or url

                sources.append(
                    {
                        "title":
                            str(title),

                        "url":
                            url,

                        "type":
                            "web"
                    }
                )

    return {
        "answer":
            answer,

        "sources":
            sources,

        "grounded":
            True
    }
