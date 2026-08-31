import re
from datetime import datetime


class WebDecision:

    def __init__(self):
        self.explicit_search = [
            "search the web",
            "search online",
            "look online",
            "look it up",
            "google",
            "search for",
            "find online",
            "check online",
            "browse the web",
            "look on the internet",
            "internet search",
        ]

        self.freshness_words = [
            "latest",
            "today",
            "current",
            "currently",
            "now",
            "recent",
            "recently",
            "this week",
            "this month",
            "2026",
            "price",
            "prices",
            "weather",
            "news",
            "stock",
            "score",
            "schedule",
            "release",
            "version",
            "update",
        ]

        self.web_domains = [
            "website",
            "webpage",
            "online",
            ".com",
            ".org",
            ".gov",
            ".edu",
            "reddit",
            "github",
            "stackoverflow",
            "wikipedia",
        ]

    def decide(self, text):

        t = text.lower().strip()

        # ----------------------------------------------------
        # 1. EXPLICIT WEB REQUEST
        # ----------------------------------------------------

        for phrase in self.explicit_search:

            if phrase in t:
                return {
                    "search": True,
                    "reason": "User explicitly requested web search.",
                    "confidence": 1.0
                }

        # ----------------------------------------------------
        # 2. TIME-SENSITIVE INFORMATION
        # ----------------------------------------------------

        for word in self.freshness_words:

            if word in t:
                return {
                    "search": True,
                    "reason":
                        "The request may require current information.",
                    "confidence": 0.95
                }

        # ----------------------------------------------------
        # 3. WEB-SPECIFIC REQUEST
        # ----------------------------------------------------

        for word in self.web_domains:

            if word in t:
                return {
                    "search": True,
                    "reason":
                        "The request appears to require web information.",
                    "confidence": 0.9
                }

        # ----------------------------------------------------
        # 4. LOCAL COMPUTER TASK
        # ----------------------------------------------------

        local_patterns = [
            r"\bopen\b",
            r"\bclose\b",
            r"\bdelete\b",
            r"\bremove\b",
            r"\bcreate\b",
            r"\brename\b",
            r"\bmove\b",
            r"\bcopy\b",
            r"\bread\b",
            r"\bfile\b",
            r"\bfolder\b",
            r"\bdesktop\b",
            r"\bcomputer\b",
            r"\bwindows\b",
            r"\bnotepad\b",
            r"\bcalculator\b",
        ]

        for pattern in local_patterns:

            if re.search(pattern, t):

                return {
                    "search": False,
                    "reason":
                        "This appears to be a local computer task.",
                    "confidence": 0.9
                }

        # ----------------------------------------------------
        # 5. DEFAULT
        # ----------------------------------------------------

        return {
            "search": False,
            "reason":
                "No strong indication that web search is necessary.",
            "confidence": 0.6
        }
