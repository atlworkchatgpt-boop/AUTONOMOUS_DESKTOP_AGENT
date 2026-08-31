import json
import re
import urllib.request
from difflib import SequenceMatcher


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:1.5b"


class SmartRouter:

    def __init__(self, runner):
        self.runner = runner

    # ========================================================
    # FUZZY HELPERS
    # ========================================================

    @staticmethod
    def similarity(a, b):
        return SequenceMatcher(
            None,
            a.lower(),
            b.lower()
        ).ratio()

    @classmethod
    def fuzzy_word(cls, word, choices, threshold=0.72):
        best = None
        best_score = 0.0

        for choice in choices:
            score = cls.similarity(
                word,
                choice
            )

            if score > best_score:
                best = choice
                best_score = score

        if best_score >= threshold:
            return best

        return None

    # ========================================================
    # NORMALIZE TYPOS
    # ========================================================

    @classmethod
    def normalize(cls, text):

        text = text.strip()

        replacements = {
            "cxhannel": "channel",
            "channle": "channel",
            "chanell": "channel",
            "chanel": "channel",
            "youtub": "youtube",
            "yutube": "youtube",
            "youube": "youtube",
            "yt": "youtube",
            "chrme": "chrome",
            "chorme": "chrome",
            "crome": "chrome",
            "gooogle": "google",
            "gogle": "google",
            "calcuator": "calculator",
            "calcualtor": "calculator",
            "notpad": "notepad",
            "explorrer": "explorer",
            "vscodee": "vscode",
        }

        words = re.findall(
            r"[A-Za-z0-9@._'/-]+",
            text.lower()
        )

        fixed = []

        known = {
            "open",
            "launch",
            "start",
            "fire",
            "up",
            "go",
            "to",
            "visit",
            "the",
            "official",
            "youtube",
            "channel",
            "search",
            "google",
            "for",
            "find",
            "chrome",
            "edge",
            "notepad",
            "calculator",
            "calc",
            "paint",
            "explorer",
            "vscode",
            "vs",
            "code",
            "screenshot",
            "take",
            "a",
            "capture",
            "screen",
            "play",
            "chess",
            "using",
            "through",
            "with",
            "account",
        }

        for word in words:

            if word in replacements:
                fixed.append(
                    replacements[word]
                )
                continue

            if word in known:
                fixed.append(word)
                continue

            match = cls.fuzzy_word(
                word,
                known,
                0.82
            )

            if match:
                fixed.append(match)
            else:
                fixed.append(word)

        return " ".join(fixed)

    # ========================================================
    # LOCAL SEMANTIC INTENT PARSER
    # ========================================================

    def semantic_intent(self, text):

        prompt = (
            "Convert the user's computer request into JSON.\n"
            "Choose ONLY one action from this list:\n"
            "open_app, youtube_channel, youtube_search, "
            "youtube_account, google_search, screenshot, "
            "chess, system_info, processes, unknown\n\n"

            "Return ONLY valid JSON.\n"
            "No markdown.\n"
            "No explanation.\n\n"

            'Format: {"action":"...", "target":"..."}\n\n'

            "Examples:\n"
            'User: open chrome\n'
            '{"action":"open_app","target":"chrome"}\n'

            'User: launch google chrome\n'
            '{"action":"open_app","target":"chrome"}\n'

            'User: open nasa yt channel\n'
            '{"action":"youtube_channel","target":"NASA"}\n'

            'User: go to the official NASA channel on youtube\n'
            '{"action":"youtube_channel","target":"NASA"}\n'

            'User: search youtube for python tutorials\n'
            '{"action":"youtube_search","target":"python tutorials"}\n'

            'User: open youtube using my account\n'
            '{"action":"youtube_account","target":""}\n'

            'User: take a screenshot\n'
            '{"action":"screenshot","target":""}\n'

            'User: play chess\n'
            '{"action":"chess","target":""}\n\n'

            "User:\n"
            + text
        )

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict command classifier. "
                        "Output JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0,
                "num_ctx": 512,
                "num_predict": 48,
                "num_thread": 2,
            }
        }

        request = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=25
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            content = (
                data
                .get("message", {})
                .get("content", "")
                .strip()
            )

            content = re.sub(
                r"^```json\s*",
                "",
                content,
                flags=re.IGNORECASE
            )

            content = re.sub(
                r"\s*```$",
                "",
                content
            )

            result = json.loads(
                content
            )

            action = result.get(
                "action",
                "unknown"
            )

            target = str(
                result.get(
                    "target",
                    ""
                )
            ).strip()

            allowed = {
                "open_app",
                "youtube_channel",
                "youtube_search",
                "youtube_account",
                "google_search",
                "screenshot",
                "chess",
                "system_info",
                "processes",
                "unknown"
            }

            if action not in allowed:
                return None

            return {
                "type": action,
                "target": target
            }

        except Exception:
            return None

    # ========================================================
    # FAST ROUTER
    # ========================================================

    def fast_route(self, text):

        normalized = self.normalize(
            text
        )

        lower = normalized.lower()

        # ----------------------------------------------------
        # YOUTUBE ACCOUNT
        # ----------------------------------------------------

        if "youtube" in lower:

            account = None

            match = re.search(
                r"(?:through|using|with)\s+([^\s]+@[^\s]+)",
                text,
                re.IGNORECASE
            )

            if match:
                account = match.group(1)

            if account and any(
                word in lower
                for word in (
                    "open",
                    "launch",
                    "start",
                    "go",
                    "visit",
                )
            ):

                return {
                    "type": "youtube_account",
                    "target": account
                }

        # ----------------------------------------------------
        # YOUTUBE CHANNEL
        # ----------------------------------------------------

        if (
            "youtube" in lower
            and "channel" in lower
        ):

            cleaned = lower

            remove = (
                "open",
                "launch",
                "start",
                "go",
                "to",
                "visit",
                "the",
                "official",
                "youtube",
                "channel",
                "on",
            )

            for word in remove:

                cleaned = re.sub(
                    r"\b"
                    + re.escape(word)
                    + r"\b",
                    " ",
                    cleaned
                )

            words = re.findall(
                r"[A-Za-z0-9']+",
                cleaned
            )

            words = [
                word
                for word in words
                if len(word) >= 2
            ]

            if words:

                return {
                    "type": "youtube_channel",
                    "target": " ".join(words)
                }

        # ----------------------------------------------------
        # YOUTUBE SEARCH
        # ----------------------------------------------------

        match = re.match(
            r".*youtube.*?"
            r"(?:search|find)\s+(?:for\s+)?(.+)$",
            lower
        )

        if match:

            return {
                "type": "youtube_search",
                "target": match.group(1).strip()
            }

        # ----------------------------------------------------
        # GOOGLE
        # ----------------------------------------------------

        match = re.match(
            r"^(?:search google for|google|search for)\s+(.+)$",
            normalized,
            re.IGNORECASE
        )

        if match:

            return {
                "type": "google_search",
                "target": match.group(1).strip()
            }

        # ----------------------------------------------------
        # SCREENSHOT
        # ----------------------------------------------------

        if (
            "screenshot" in lower
            or (
                "screen" in lower
                and (
                    "capture" in lower
                    or "take" in lower
                )
            )
        ):

            return {
                "type": "screenshot",
                "target": ""
            }

        # ----------------------------------------------------
        # CHESS
        # ----------------------------------------------------

        if "chess" in lower:

            return {
                "type": "chess",
                "target": ""
            }

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        if (
            "system info" in lower
            or "system information" in lower
            or "check my pc" in lower
        ):

            return {
                "type": "system_info",
                "target": ""
            }

        # ----------------------------------------------------
        # PROCESSES
        # ----------------------------------------------------

        if (
            "running processes" in lower
            or "running programs" in lower
            or "what is running" in lower
        ):

            return {
                "type": "processes",
                "target": ""
            }

        # ----------------------------------------------------
        # APPLICATIONS
        # ----------------------------------------------------

        apps = {
            "chrome": "start chrome",
            "google chrome": "start chrome",
            "edge": "start msedge",
            "microsoft edge": "start msedge",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
        }

        if any(
            phrase in lower
            for phrase in (
                "open",
                "launch",
                "start",
                "fire up",
            )
        ):

            for name, command in apps.items():

                if name in lower:

                    return {
                        "type": "open_app",
                        "target": command
                    }

        return None

    # ========================================================
    # PUBLIC ROUTER
    # ========================================================

    def handle(
        self,
        text,
    ):

        # First attempt is very fast.
        result = self.fast_route(
            text
        )

        if result is not None:
            return True, result

        # Only ambiguous commands reach the local model.
        result = self.semantic_intent(
            text
        )

        if result is not None:

            if result["type"] != "unknown":
                return True, result

        return False, None

    # Compatibility alias.
    route = handle