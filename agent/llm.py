import ollama


# ============================================================
# LOCAL MODEL CONFIGURATION
# ============================================================

FAST_MODEL = "qwen2.5:0.5b-instruct"
SMART_MODEL = "qwen2.5:0.5b-instruct"


SYSTEM_PROMPT = """
You are the reasoning core of a local Autonomous Desktop AI.

You are running entirely on the user's computer.

Your responsibilities:

- understand the user's goal
- reason about the task
- break complex tasks into steps
- use available tools when requested by the controller
- inspect real tool results
- detect failures
- never invent results
- never claim an action succeeded without evidence
- distinguish facts from assumptions
- verify important operations
- keep responses concise and useful

IMPORTANT:

You do not directly control Windows.

Python tools perform actions.

Therefore NEVER claim:

"I opened Notepad"

unless the tool result confirms it.

NEVER claim:

"I created the file"

unless the tool result confirms it.

NEVER invent:

- files
- directories
- application state
- command output
- system information
- tool results
- successful actions

If a tool fails, acknowledge the failure and decide whether
another action is appropriate.
"""


class LocalBrain:

    def __init__(self, model=None):

        self.model = model or FAST_MODEL


    def choose_model(self, message):

        text = message.lower()

        complex_words = [
            "debug",
            "program",
            "code",
            "analyze",
            "architecture",
            "complex",
            "research",
            "explain deeply",
            "design",
            "develop",
            "multiple steps",
            "solve"
        ]

        if any(word in text for word in complex_words):
            return SMART_MODEL

        return FAST_MODEL


    def ask(self, message, context=""):

        model = self.choose_model(message)

        if context:

            prompt = f"""
RELEVANT KNOWLEDGE:

{context}

USER REQUEST:

{message}
"""

        else:

            prompt = message


        response = ollama.chat(

            model=model,

            messages=[

                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            options={

                "temperature": 0.15,

                "num_predict": 512

            }

        )

        return response["message"]["content"]


    def chat(self, messages):

        response = ollama.chat(

            model=self.model,

            messages=messages,

            options={

                "temperature": 0.15,

                "num_predict": 512

            }

        )

        return response["message"]["content"]

