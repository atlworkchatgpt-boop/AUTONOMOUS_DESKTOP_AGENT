from ddgs import DDGS


def search_web(query, max_results=5):
    try:
        results = DDGS().text(
            query,
            max_results=max_results,
        )

        cleaned = []

        for item in results or []:
            cleaned.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })

        return {
            "ok": True,
            "results": cleaned,
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }