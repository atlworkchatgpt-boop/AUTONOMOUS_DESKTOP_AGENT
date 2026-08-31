import urllib.parse
import urllib.request
import json


def search_web(query, limit=5):

    try:

        encoded = urllib.parse.quote(query)

        url = (
            "https://api.duckduckgo.com/"
            "?q="
            + encoded
            + "&format=json"
            + "&no_html=1"
            + "&skip_disambig=1"
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                "AutonomousDesktopAI/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=5
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8",
                    errors="replace"
                )
            )

        results = []

        abstract = data.get(
            "AbstractText",
            ""
        )

        if abstract:

            results.append({
                "title": data.get(
                    "Heading",
                    "Web result"
                ),
                "text": abstract,
                "url": data.get(
                    "AbstractURL",
                    ""
                )
            })

        for item in data.get(
            "RelatedTopics",
            []
        )[:limit]:

            if "Text" in item:

                results.append({
                    "title": item.get(
                        "Text",
                        ""
                    )[:100],
                    "text": item.get(
                        "Text",
                        ""
                    ),
                    "url": item.get(
                        "FirstURL",
                        ""
                    )
                })

        return results[:limit]

    except Exception as e:

        return [{
            "title": "Search unavailable",
            "text": str(e),
            "url": ""
        }]
