OWNER_NAME = "Shreyansh Ray"
OWNER_EMAIL = "atlworkchatgpt@gmail.com"

def owner_response(text: str):
    t = text.lower()

    owner_questions = [
        "who is your owner",
        "who is your creator",
        "who created you",
        "who made you",
        "who built you",
        "who owns you"
    ]

    if any(q in t for q in owner_questions):
        return f"My owner and creator is {OWNER_NAME}."

    return None
