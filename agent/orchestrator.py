import json
import re
import urllib.request
from pathlib import Path

from agent.memory import (
    context_for,
    remember,
)

from agent.web_tools import (
    search_web,
    source_text,
)


class UnifiedOrchestrator:

    def __init__(
        self,
        root,
        router,
        runner,
        brain,
        logger,
        chess_callback,
        project_dir,
    ):

        self.root = root
        self.router = router
        self.runner = runner
        self.brain = brain
        self.logger = logger
        self.chess_callback = chess_callback
        self.project_dir = Path(
            project_dir
        ).resolve()

        self.stopped = False

    # ========================================================
    # MAIN
    # ========================================================

    def process(
        self,
        text,
    ):

        self.stopped = False

        # ----------------------------------------------------
        # MULTI-STEP REQUEST
        # ----------------------------------------------------

        if self.is_complex_request(
            text
        ):

            return self.run_complex(
                text
            )

        # ----------------------------------------------------
        # FAST ROUTER
        # ----------------------------------------------------

        handled, route = (
            self.router.handle(
                text
            )
        )

        if handled:

            return self.execute_route(
                text,
                route
            )

        # ----------------------------------------------------
        # WEB-FIRST QUESTIONS
        # ----------------------------------------------------

        if self.should_search(
            text
        ):

            return self.web_answer(
                text
            )

        # ----------------------------------------------------
        # NORMAL AI
        # ----------------------------------------------------

        memory = context_for(
            text
        )

        ok, answer = self.brain.ask(
            text,
            memory_context=memory,
        )

        self._remember(
            text,
            "chat",
            "local_ai",
            answer,
            ok,
        )

        return ok, answer

    # ========================================================
    # COMPLEX REQUEST DETECTION
    # ========================================================

    @staticmethod
    def is_complex_request(
        text,
    ):

        lower = text.lower()

        number_count = len(
            re.findall(
                r"(?m)^\s*\d+\.",
                text,
            )
        )

        markers = (
            "perform the following tasks",
            "advanced assistant test mode",
            "step 1",
            "step 2",
            "then",
            "finally",
            "and after that",
            "in order",
            "report the result",
        )

        return (
            number_count >= 3
            or any(
                marker in lower
                for marker in markers
            )
        )

    # ========================================================
    # COMPLEX TASK
    # ========================================================

    def run_complex(
        self,
        text,
    ):

        self.logger(
            "AI: \U0001F9E0 Complex task detected. "
            "Using the unified task engine."
        )

        routes = []

        lower = text.lower()

        # System.
        if (
            "system" in lower
            or "operating system" in lower
            or "ram" in lower
            or "cpu" in lower
        ):

            routes.append(
                (
                    "System information",
                    {
                        "type": "system"
                    },
                )
            )

        # Ollama.
        if "ollama" in lower:

            routes.append(
                (
                    "Ollama check",
                    {
                        "type": "ollama"
                    },
                )
            )

        # Python release.
        if "python" in lower:

            routes.append(
                (
                    "Python web verification",
                    {
                        "type": "web",
                        "query": (
                            "latest Python release "
                            "site:python.org"
                        ),
                    },
                )
            )

        # Chrome.
        if "chrome" in lower:

            routes.append(
                (
                    "Open Chrome",
                    {
                        "type": "open_app",
                        "command": "start chrome",
                    },
                )
            )

        # YouTube.
        if "youtube" in lower:

            channel = "NASA"

            match = re.search(
                r"(.+?)\s+channel\s+on\s+youtube",
                lower,
            )

            if match:

                candidate = match.group(
                    1
                )

                candidate = re.sub(
                    r"\b(open|the|official)\b",
                    " ",
                    candidate,
                )

                candidate = " ".join(
                    candidate.split()
                ).strip()

                if candidate:
                    channel = candidate

            routes.append(
                (
                    "Open YouTube channel",
                    {
                        "type": "youtube_channel",
                        "name": channel,
                    },
                )
            )

        # Screenshot.
        if "screenshot" in lower:

            routes.append(
                (
                    "Desktop screenshot",
                    {
                        "type": "screenshot"
                    },
                )
            )

        # Project.
        if (
            "inspect this project" in lower
            or "project structure" in lower
            or "main entry point" in lower
        ):

            routes.append(
                (
                    "Inspect project",
                    {
                        "type": "project"
                    },
                )
            )

        # Learning.
        if (
            "learning database" in lower
            or "previous failures" in lower
            or "successful actions" in lower
        ):

            routes.append(
                (
                    "Read learning memory",
                    {
                        "type": "memory"
                    },
                )
            )

        # Chess.
        if "chess" in lower:

            routes.append(
                (
                    "Start chess",
                    {
                        "type": "chess"
                    },
                )
            )

        # Execute sequentially.
        results = []

        for index, (
            name,
            route,
        ) in enumerate(
            routes,
            1,
        ):

            if self.stopped:
                break

            self.logger(
                f"STEP {index}/{len(routes)}: {name}"
            )

            ok, detail = (
                self.execute_complex_route(
                    text,
                    route,
                )
            )

            results.append(
                {
                    "name": name,
                    "ok": ok,
                    "detail": detail,
                }
            )

            # Safe recovery only.
            if (
                not ok
                and route.get(
                    "type"
                ) in {
                    "youtube_channel",
                    "web",
                }
            ):

                self.logger(
                    f"AI: Attempting safe recovery for {name}."
                )

                retry_ok, retry_detail = (
                    self.recover(
                        text,
                        route,
                    )
                )

                if retry_ok:

                    ok = True
                    detail = (
                        "Recovery succeeded: "
                        + retry_detail
                    )

                    results[-1] = {
                        "name": name,
                        "ok": True,
                        "detail": detail,
                    }

        self.final_report(
            results
        )

        return True, (
            "Complex task completed."
        )

    # ========================================================
    # ROUTE EXECUTION
    # ========================================================

    def execute_route(
        self,
        request,
        route,
    ):

        route_type = route.get(
            "type"
        )

        try:

            if route_type == "chess":

                self.root.after(
                    0,
                    self.chess_callback
                )

                detail = (
                    "Chess launch requested."
                )

                self._remember(
                    request,
                    "computer",
                    "chess",
                    detail,
                    True,
                )

                return True, detail

            if route_type == "youtube_account":

                result = self.runner.youtube_account(
                    route.get("account")
                )

                return self._result(
                    request,
                    "youtube",
                    "youtube_account",
                    result,
                )

            if route_type == "youtube_channel":

                result = self.runner.youtube_channel(
                    route["name"]
                )

                return self._result(
                    request,
                    "youtube",
                    "youtube_channel",
                    result,
                )

            if route_type == "youtube_search":

                result = self.runner.youtube_search(
                    route["query"]
                )

                return self._result(
                    request,
                    "youtube",
                    "youtube_search",
                    result,
                )

            if route_type == "google":

                result = self.runner.search_google(
                    route["query"]
                )

                return self._result(
                    request,
                    "browser",
                    "google_search",
                    result,
                )

            if route_type == "open_app":

                result = self.runner.open_app(
                    route["command"]
                )

                return self._result(
                    request,
                    "computer",
                    "open_app",
                    result,
                )

            if route_type == "screenshot":

                result = self.runner.screenshot()

                return self._result(
                    request,
                    "computer",
                    "screenshot",
                    result,
                )

            if route_type == "system":

                result = self.runner.system_info()

                return self._result(
                    request,
                    "computer",
                    "system_info",
                    result,
                )

            if route_type == "processes":

                result = self.runner.processes()

                return self._result(
                    request,
                    "computer",
                    "process_list",
                    result,
                )

        except Exception as exc:

            self._remember(
                request,
                route_type,
                route_type,
                str(exc),
                False,
            )

            return False, str(exc)

        return False, (
            "Unknown route."
        )

    # ========================================================
    # COMPLEX ROUTES
    # ========================================================

    def execute_complex_route(
        self,
        request,
        route,
    ):

        route_type = route.get(
            "type"
        )

        if route_type == "project":

            return self.inspect_project(
                request
            )

        if route_type == "memory":

            return self.read_memory(
                request
            )

        if route_type == "ollama":

            return self.ollama_check(
                request
            )

        if route_type == "web":

            return self.web_answer(
                request,
                forced_query=route.get(
                    "query"
                ),
            )

        return self.execute_route(
            request,
            route,
        )

    # ========================================================
    # WEB
    # ========================================================

    def should_search(
        self,
        text,
    ):

        lower = text.lower()

        triggers = (
            "latest",
            "current",
            "today",
            "recent",
            "news",
            "price",
            "release",
            "version",
            "weather",
            "who is",
            "what happened",
            "search the web",
            "look up",
            "online",
            "according to",
        )

        return any(
            trigger in lower
            for trigger in triggers
        )

    def web_answer(
        self,
        request,
        forced_query=None,
    ):

        query = (
            forced_query
            or request
        )

        result = search_web(
            query,
            max_results=5,
        )

        if not result.get(
            "ok",
            False,
        ):

            detail = result.get(
                "error",
                "Web search failed."
            )

            self._remember(
                request,
                "web",
                "search",
                detail,
                False,
            )

            return False, detail

        sources = result.get(
            "results",
            []
        )

        if not sources:

            return False, (
                "No useful web results were found."
            )

        evidence = source_text(
            sources
        )

        # Keep the model input small.
        evidence = evidence[
            :9000
        ]

        answer_prompt = (
            "Answer this question using ONLY the "
            "web evidence below.\n\n"
            "Question:\n"
            + request
            + "\n\n"
            "Evidence:\n"
            + evidence
            + "\n\n"
            "Rules:\n"
            "- Prefer authoritative sources.\n"
            "- Do not invent facts.\n"
            "- For latest/current questions, "
            "prefer the newest evidence.\n"
            "- Say when evidence is insufficient.\n"
            "- Give the direct answer first."
        )

        ok, answer = self.brain.ask(
            answer_prompt,
        )

        if ok:

            self._remember(
                request,
                "web",
                "research_and_summarize",
                answer,
                True,
            )

            return True, (
                answer
                + "\n\nSources:\n"
                + "\n".join(
                    item.get(
                        "url",
                        "",
                    )
                    for item in sources
                    if item.get(
                        "url",
                        "",
                    )
                )
            )

        # If the local model fails, return the actual evidence
        # rather than inventing an answer.
        fallback = (
            "I found these web sources, "
            "but the local summarizer failed:\n\n"
            + evidence
        )

        self._remember(
            request,
            "web",
            "research_and_summarize",
            fallback,
            False,
        )

        return False, fallback

    # ========================================================
    # OLLAMA
    # ========================================================

    def ollama_check(
        self,
        request,
    ):

        try:

            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/tags",
                method="GET",
            )

            with urllib.request.urlopen(
                req,
                timeout=5,
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            models = [
                item.get(
                    "name",
                    "",
                )
                for item in data.get(
                    "models",
                    []
                )
            ]

            detail = (
                "Ollama is reachable.\n"
                "Models: "
                + ", ".join(
                    models[:10]
                )
            )

            self._remember(
                request,
                "system",
                "ollama_check",
                detail,
                True,
            )

            return True, detail

        except Exception as exc:

            detail = str(exc)

            self._remember(
                request,
                "system",
                "ollama_check",
                detail,
                False,
            )

            return False, detail

    # ========================================================
    # PROJECT
    # ========================================================

    def inspect_project(
        self,
        request,
    ):

        root = self.project_dir

        if not root.exists():

            return False, (
                f"Project not found: {root}"
            )

        ignored = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
        }

        files = []

        try:

            for path in root.rglob("*"):

                relative = path.relative_to(
                    root
                )

                if any(
                    part in ignored
                    for part in relative.parts
                ):
                    continue

                if path.is_file():

                    files.append(
                        str(relative)
                    )

            files.sort()

            detail = (
                f"Project: {root}\n"
                f"Files: {len(files)}\n\n"
                + "\n".join(
                    files[:200]
                )
            )

            self._remember(
                request,
                "files",
                "project_inspection",
                detail,
                True,
            )

            return True, detail

        except Exception as exc:

            self._remember(
                request,
                "files",
                "project_inspection",
                str(exc),
                False,
            )

            return False, str(exc)

    # ========================================================
    # MEMORY
    # ========================================================

    def read_memory(
        self,
        request,
    ):

        try:

            from agent.memory import recent

            rows = recent(
                10
            )

            if not rows:

                return True, (
                    "Learning memory is empty."
                )

            lines = [
                "Recent agent experiences:"
            ]

            for row in rows:

                state = (
                    "SUCCESS"
                    if row[4]
                    else "FAILURE"
                )

                lines.append(
                    (
                        f"[{state}] "
                        f"{row[0]} -> "
                        f"{row[2]} -> "
                        f"{row[3]}"
                    )
                )

            return True, "\n".join(
                lines
            )

        except Exception as exc:

            return False, str(exc)

    # ========================================================
    # RECOVERY
    # ========================================================

    def recover(
        self,
        request,
        route,
    ):

        route_type = route.get(
            "type"
        )

        # Safe web retry with a better query.
        if route_type == "web":

            query = route.get(
                "query",
                request,
            )

            improved = (
                query
                + " official authoritative source"
            )

            result = search_web(
                improved,
                max_results=5,
            )

            if result.get(
                "ok",
                False
            ):

                sources = result.get(
                    "results",
                    []
                )

                if sources:

                    evidence = source_text(
                        sources
                    )[:7000]

                    return True, evidence

            return False, (
                "Recovery web search failed."
            )

        # Safe YouTube retry: search instead of directly
        # opening a guessed URL.
        if route_type == "youtube_channel":

            name = route.get(
                "name",
                "",
            )

            result = self.runner.youtube_search(
                name
                + " official channel"
            )

            if result.get(
                "ok",
                False
            ):

                return True, result.get(
                    "message",
                    "YouTube search opened."
                )

            return False, result.get(
                "message",
                "YouTube recovery failed."
            )

        return False, (
            "No safe recovery strategy exists."
        )

    # ========================================================
    # RESULT
    # ========================================================

    def _result(
        self,
        request,
        category,
        action,
        result,
    ):

        if not isinstance(
            result,
            dict,
        ):

            ok = bool(result)
            detail = str(result)

        else:

            ok = bool(
                result.get(
                    "ok",
                    False,
                )
            )

            detail = str(
                result.get(
                    "message",
                    result.get(
                        "error",
                        result,
                    ),
                )
            )

        self._remember(
            request,
            category,
            action,
            detail,
            ok,
        )

        return ok, detail

    # ========================================================
    # MEMORY
    # ========================================================

    def _remember(
        self,
        request,
        category,
        action,
        result,
        success,
    ):

        try:

            remember(
                request,
                category,
                action,
                result,
                success,
            )

        except Exception:

            pass

    # ========================================================
    # REPORT
    # ========================================================

    def final_report(
        self,
        results,
    ):

        successful = [
            item
            for item in results
            if item["ok"]
        ]

        failed = [
            item
            for item in results
            if not item["ok"]
        ]

        lines = [
            "",
            "========================================",
            "TASK COMPLETE",
            "========================================",
            "",
            f"Attempted: {len(results)}",
            f"Successful: {len(successful)}",
            f"Failed: {len(failed)}",
            "",
        ]

        for item in results:

            state = (
                "SUCCESS"
                if item["ok"]
                else "FAILED"
            )

            lines.append(
                f"[{state}] {item['name']}"
            )

            lines.append(
                f"  {item['detail']}"
            )

        self.logger(
            "AI:\n"
            + "\n".join(lines)
        )

    def stop(self):

        self.stopped = True
