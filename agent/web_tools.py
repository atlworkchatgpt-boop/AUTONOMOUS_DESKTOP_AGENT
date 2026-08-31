import re
import urllib.request


def _clean(
    text,
):

    text = re.sub(
        r"\s+",
        " ",
        text or "",
    )

    return text.strip()


def search_web(
    query,
    max_results=5,
):

    try:

        from ddgs import DDGS

    except Exception as exc:

        return {
            "ok": False,
            "error": (
                "ddgs is unavailable: "
                + str(exc)
            ),
            "results": [],
        }

    try:

        raw = list(
            DDGS().text(
                query,
                max_results=max_results,
            )
        )

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
            "results": [],
        }

    results = []

    for item in raw:

        title = _clean(
            item.get(
                "title",
                "",
            )
        )

        url = item.get(
            "href",
            "",
        )

        snippet = _clean(
            item.get(
                "body",
                "",
            )
        )

        if title or snippet:

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

    return {
        "ok": True,
        "results": results,
    }


def source_text(
    results,
):

    blocks = []

    for item in results:

        blocks.append(
            (
                "TITLE: "
                + item.get("title", "")
                + "\n"
                "URL: "
                + item.get("url", "")
                + "\n"
                "TEXT: "
                + item.get("snippet", "")
            )
        )

    return "\n\n".join(
        blocks
    )