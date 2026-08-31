from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
)


class BrowserController:

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

        if not self.authentication.require_start_auth(
            "Starting the browser."
        ):

            return None

        self.playwright = (
            sync_playwright().start()
        )

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

        return self.page

    def search(
        self,
        query,
    ):

        if not self.authentication.require_action_auth(
            f"Browser search:\n{query}"
        ):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Browser search cancelled.",
            }

        page = self._ensure_browser()

        if page is None:

            return {
                "ok": False,
                "cancelled": True,
                "message": "Browser launch cancelled.",
            }

        url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return {
            "ok": True,
            "query": query,
            "url": page.url,
            "title": page.title(),
        }

    def open_url(
        self,
        url,
    ):

        if not self.authentication.require_action_auth(
            f"Opening browser URL:\n{url}"
        ):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Browser navigation cancelled.",
            }

        page = self._ensure_browser()

        if page is None:

            return {
                "ok": False,
                "cancelled": True,
            }

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return {
            "ok": True,
            "url": page.url,
            "title": page.title(),
        }

    def back(self):

        if not self.authentication.require_action_auth(
            "Browser back navigation."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        page.go_back()

        return {
            "ok": True,
            "url": page.url,
        }

    def forward(self):

        if not self.authentication.require_action_auth(
            "Browser forward navigation."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        page.go_forward()

        return {
            "ok": True,
            "url": page.url,
        }

    def refresh(self):

        if not self.authentication.require_action_auth(
            "Browser refresh."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        page.reload()

        return {
            "ok": True,
            "url": page.url,
        }

    def type_text(
        self,
        selector,
        text,
    ):

        if not self.authentication.require_action_auth(
            "Typing into a browser page."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        page.locator(
            selector
        ).fill(
            text
        )

        return {
            "ok": True,
        }

    def click(
        self,
        selector,
    ):

        if not self.authentication.require_action_auth(
            "Clicking in a browser page."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        page.locator(
            selector
        ).click(
            timeout=15000
        )

        return {
            "ok": True,
        }

    def read_page(self):

        if not self.authentication.require_action_auth(
            "Reading browser page contents."
        ):

            return {
                "ok": False,
                "cancelled": True,
            }

        page = self._ensure_browser()

        if page is None:
            return {
                "ok": False,
                "cancelled": True,
            }

        text = page.locator(
            "body"
        ).inner_text()

        return {
            "ok": True,
            "url": page.url,
            "title": page.title(),
            "text": text[:30000],
        }

    def close_browser(self):

        if self.browser:

            try:
                self.browser.close()
            except Exception:
                pass

        if self.playwright:

            try:
                self.playwright.stop()
            except Exception:
                pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None