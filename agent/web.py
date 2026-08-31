import requests
from urllib.parse import quote
import re


def web_search(query, limit=5):

    try:

        url = (
            "https://html.duckduckgo.com/html/?q="
            + quote(query)
        )

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    "Mozilla/5.0"
            },
            timeout=8
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error":
                    "Search service returned HTTP "
                    + str(response.status_code)
            }

        html = response.text

        blocks = re.findall(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            re.S
        )

        results = []

        for href, title in blocks[:limit]:

            title = re.sub(
                "<.*?>",
                "",
                title
            )

            results.append({
                "title": title,
                "url": href
            })

        return {
            "success": True,
            "results": results
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
