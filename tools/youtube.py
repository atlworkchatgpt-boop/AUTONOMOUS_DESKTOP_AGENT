from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright


class YouTubeController:

    def __init__(
        self,
        authentication,
    ):

        self.authentication = authentication

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _ensure_browser(self):

        if self.page is not None:
            return self.page

        # IMPORTANT:
        # YouTube is an action performed by the running AI,
        # so use gngai, NOT gngaistart.
        if not self.authentication.require_action(
            "Starting the browser for YouTube."
        ):
            return None

        self.playwright = sync_playwright().start()

        try:

            self.browser = (
                self.playwright.chromium.launch(
                    channel="chrome",
                    headless=False,
                )
            )

        except Exception:

            self.browser = (
                self.playwright.chromium.launch(
                    headless=False,
                )
            )

        self.context = (
            self.browser.new_context()
        )

        self.page = (
            self.context.new_page()
        )

        self.page.set_default_timeout(
            12000
        )

        return self.page

    def search(
        self,
        query,
    ):

        page = self._ensure_browser()

        if page is None:

            return {
                "ok": False,
                "message": "YouTube action cancelled.",
            }

        try:

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            return {
                "ok": True,
                "message": (
                    f"YouTube search opened for: {query}"
                ),
                "url": page.url,
            }

        except Exception as exc:

            return {
                "ok": False,
                "message": (
                    f"YouTube search failed: {exc}"
                ),
            }

    def open_channel(
        self,
        channel_name,
    ):

        page = self._ensure_browser()

        if page is None:

            return {
                "ok": False,
                "message": "YouTube action cancelled.",
            }

        try:

            search_url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(channel_name)
            )

            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            try:

                page.wait_for_timeout(
                    2000
                )

            except Exception:
                pass

            # ------------------------------------------------
            # Try actual channel result elements first.
            # ------------------------------------------------

            selectors = (
                "ytd-channel-renderer a#main-link",
                "ytd-channel-renderer a[href*='/@']",
                "ytd-channel-renderer a[href*='/channel/']",
            )

            for selector in selectors:

                try:

                    links = page.locator(
                        selector
                    )

                    count = links.count()

                    for index in range(
                        min(count, 15)
                    ):

                        link = links.nth(
                            index
                        )

                        text = ""

                        try:

                            text = link.inner_text(
                                timeout=2500
                            ).strip()

                        except Exception:

                            pass

                        href = link.get_attribute(
                            "href"
                        )

                        if not href:
                            continue

                        target_words = [
                            word.lower()
                            for word in
                            channel_name.split()
                            if len(word) >= 3
                        ]

                        combined = (
                            text
                            + " "
                            + href
                        ).lower()

                        matches = all(
                            word in combined
                            for word in target_words
                        )

                        if matches:

                            if href.startswith("/"):
                                href = (
                                    "https://www.youtube.com"
                                    + href
                                )

                            page.goto(
                                href,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )

                            return {
                                "ok": True,
                                "message": (
                                    f"Opened YouTube channel: "
                                    f"{channel_name}"
                                ),
                                "url": page.url,
                            }

                except Exception:
                    continue

            # ------------------------------------------------
            # Fallback: search for channel links.
            # ------------------------------------------------

            selectors = (
                "a[href*='/@']",
                "a[href*='/channel/']",
            )

            target_words = [
                word.lower()
                for word in channel_name.split()
                if len(word) >= 3
            ]

            for selector in selectors:

                try:

                    links = page.locator(
                        selector
                    )

                    count = links.count()

                    for index in range(
                        min(count, 30)
                    ):

                        link = links.nth(
                            index
                        )

                        href = link.get_attribute(
                            "href"
                        )

                        if not href:
                            continue

                        text = ""

                        try:

                            text = link.inner_text(
                                timeout=2000
                            ).strip()

                        except Exception:

                            pass

                        combined = (
                            text
                            + " "
                            + href
                        ).lower()

                        if all(
                            word in combined
                            for word in target_words
                        ):

                            if href.startswith("/"):
                                href = (
                                    "https://www.youtube.com"
                                    + href
                                )

                            page.goto(
                                href,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )

                            return {
                                "ok": True,
                                "message": (
                                    f"Opened YouTube channel: "
                                    f"{channel_name}"
                                ),
                                "url": page.url,
                            }

                except Exception:
                    continue

            return {
                "ok": False,
                "message": (
                    f"I searched YouTube for "
                    f"'{channel_name}', but could not "
                    "confidently identify the channel."
                ),
                "url": page.url,
            }

        except Exception as exc:

            return {
                "ok": False,
                "message": (
                    f"YouTube channel search failed: {exc}"
                ),
            }

    def close(self):

        try:

            if self.browser:
                self.browser.close()

        except Exception:
            pass

        try:

            if self.playwright:
                self.playwright.stop()

        except Exception:
            pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None