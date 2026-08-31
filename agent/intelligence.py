import os
import re
import subprocess
import webbrowser

from agent.config import MODEL_PREFERENCE
from agent.memory.memory import Memory
from agent.tools.desktop import (
    open_application,
    open_url,
    list_directory,
    read_text_file
)
from agent.tools.web import search_web


class Intelligence:

    def __init__(self):

        self.memory = Memory()

        self.ollama = None
        self.model = None
        self.initialized = False


    # ========================================================
    # LAZY OLLAMA INITIALIZATION
    # ========================================================

    def initialize_model(self):

        if self.initialized:
            return self.model

        self.initialized = True

        try:

            import ollama

            self.ollama = ollama

            response = ollama.list()

            installed = []

            # New ollama client format
            for item in response.get(
                "models",
                []
            ):

                name = getattr(
                    item,
                    "model",
                    None
                )

                if name is None:

                    name = getattr(
                        item,
                        "name",
                        None
                    )

                if name is None and isinstance(
                    item,
                    dict
                ):

                    name = (
                        item.get("model")
                        or item.get("name")
                    )

                if name:
                    installed.append(name)

            # Exact match first
            for preferred in MODEL_PREFERENCE:

                if preferred in installed:

                    self.model = preferred
                    return self.model

            # Prefix fallback
            for preferred in MODEL_PREFERENCE:

                base = preferred.split(":")[0]

                for installed_name in installed:

                    if installed_name.startswith(
                        base
                    ):

                        self.model = installed_name
                        return self.model

            return None

        except Exception:

            self.ollama = None
            self.model = None
            return None


    # ========================================================
    # WEB DECISION
    # ========================================================

    def should_search_web(self, message):

        text = message.lower()

        web_words = [
            "latest",
            "today",
            "current",
            "recent",
            "news",
            "price",
            "weather",
            "score",
            "update",
            "search web",
            "search the web",
            "look online",
            "internet"
        ]

        return any(
            word in text
            for word in web_words
        )


    # ========================================================
    # LLM
    # ========================================================

    def ask_llm(
        self,
        message,
        web_context=""
    ):

        model = self.initialize_model()

        if not model:

            return None

        history = self.memory.recent(8)

        messages = [
            {
                "role": "system",
                "content":
                """
You are the reasoning core of an autonomous desktop assistant.

Be useful, concise and intelligent.

You can reason about:
- normal questions
- computer tasks
- files
- applications
- web information
- planning
- troubleshooting

Important:
Never claim a computer action happened unless the program
actually executed it.

If web information is supplied, use it and distinguish it
from your own knowledge.

If the user asks for a computer action, explain what you
can safely do.

Do not make up tool results.
"""
            }
        ]

        for item in history:

            role = item.get(
                "role",
                "user"
            )

            if role not in [
                "user",
                "assistant"
            ]:
                continue

            messages.append({
                "role": role,
                "content": item.get(
                    "content",
                    ""
                )
            })

        if web_context:

            message = (
                message
                + "\n\nWEB RESULTS:\n"
                + web_context
            )

        messages.append({
            "role": "user",
            "content": message
        })

        try:

            result = self.ollama.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": 0.25,
                    "num_ctx": 2048
                }
            )

            content = result["message"]["content"]

            return content.strip()

        except Exception:

            return None


    # ========================================================
    # FAST COMPUTER INTENTS
    # ========================================================

    def computer_action(
        self,
        message
    ):

        text = message.lower().strip()


        # NOTEPAD

        if (
            "open notepad" in text
            or text == "notepad"
        ):

            result = open_application(
                "notepad.exe"
            )

            if result["success"]:

                return "Opened Notepad."

            return (
                "I couldn't open Notepad: "
                + result["error"]
            )


        # CALCULATOR

        if (
            "open calculator" in text
            or "open calc" in text
        ):

            result = open_application(
                "calc.exe"
            )

            if result["success"]:

                return "Opened Calculator."

            return (
                "I couldn't open Calculator: "
                + result["error"]
            )


        # EXPLORER

        if (
            "open file explorer" in text
            or "open explorer" in text
        ):

            result = open_application(
                "explorer.exe"
            )

            if result["success"]:

                return "Opened File Explorer."

            return (
                "I couldn't open File Explorer: "
                + result["error"]
            )


        # CHROME

        if (
            "open chrome" in text
        ):

            result = open_application(
                "start chrome"
            )

            if result["success"]:

                return "Opened Chrome."

            return (
                "I couldn't open Chrome: "
                + result["error"]
            )


        # YOUTUBE

        if (
            "open youtube" in text
        ):

            open_url(
                "https://www.youtube.com"
            )

            return "Opened YouTube."


        # GOOGLE

        if (
            "open google" in text
        ):

            open_url(
                "https://www.google.com"
            )

            return "Opened Google."


        # LIST FILES

        if (
            "list files" in text
            or "show files" in text
            or "what files are here" in text
        ):

            result = list_directory(".")

            if not result["success"]:

                return result["error"]

            names = [
                item["name"]
                for item in result["items"]
            ]

            if not names:

                return "The current folder is empty."

            return (
                "Files and folders:\n\n"
                + "\n".join(
                    names[:80]
                )
            )

        return None


    # ========================================================
    # MAIN RESPONSE
    # ========================================================

    def respond(self, message):

        message = message.strip()

        if not message:

            return "Tell me what you want to do."


        self.memory.add(
            "user",
            message
        )


        # Fast deterministic commands first.

        action = self.computer_action(
            message
        )

        if action:

            self.memory.add(
                "assistant",
                action
            )

            return action


        # Web only when appropriate.

        web_context = ""

        if self.should_search_web(
            message
        ):

            results = search_web(
                message
            )

            parts = []

            for item in results:

                parts.append(
                    item.get(
                        "title",
                        ""
                    )
                    + "\n"
                    + item.get(
                        "text",
                        ""
                    )
                )

            web_context = "\n\n".join(
                parts
            )


        # LLM.

        answer = self.ask_llm(
            message,
            web_context
        )

        if answer:

            self.memory.add(
                "assistant",
                answer
            )

            return answer


        # No model.

        answer = (
            "I couldn't start the local AI model.\n\n"
            "Run this in PowerShell to check your models:\n"
            "ollama list\n\n"
            "Your fast model should be:\n"
            "qwen2.5:1.5b-instruct-q4_0"
        )

        self.memory.add(
            "assistant",
            answer
        )

        return answer

