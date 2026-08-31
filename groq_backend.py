import os
from groq import Groq

MODEL = "openai/gpt-oss-120b"

class GroqBackend:

    def __init__(self):
        key = os.environ.get("GROQ_API_KEY")

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set."
            )

        self.client = Groq(api_key=key)

    def ask(self, messages):
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )

        if not response.choices:
            return "Groq returned no response."

        text = response.choices[0].message.content

        if not text:
            return "Groq returned an empty response."

        return str(text).strip()


def test():
    backend = GroqBackend()

    result = backend.ask([
        {
            "role": "system",
            "content": (
                "You are a helpful desktop AI assistant. "
                "Be accurate and concise. "
                "Never claim information is current unless "
                "it has actually been verified."
            )
        },
        {
            "role": "user",
            "content": "Reply with exactly: GROQ BACKEND WORKING"
        }
    ])

    print(result)


if __name__ == "__main__":
    test()
