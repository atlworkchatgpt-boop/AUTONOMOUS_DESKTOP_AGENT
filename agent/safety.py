from config.config import (
    DANGEROUS_COMMAND_WORDS,
    PERSONAL_INFO_KEYWORDS,
)


def dangerous_command(
    command,
):

    lowered = command.lower()

    cleaned = (
        lowered
        .replace("&", " ")
        .replace("|", " ")
        .replace(";", " ")
        .replace(",", " ")
    )

    tokens = cleaned.split()

    for word in DANGEROUS_COMMAND_WORDS:

        if word in tokens:
            return True

        if word in lowered:
            return True

    return False


def personal_info_requested(
    text,
):

    lowered = text.lower()

    return any(
        phrase in lowered
        for phrase in PERSONAL_INFO_KEYWORDS
    )