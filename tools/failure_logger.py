from agent.learning import (
    record_failure,
    record_success,
)


def log_failure(
    request,
    action,
    arguments=None,
    error=""
):

    try:

        record_failure(
            request,
            action,
            arguments,
            error
        )

    except Exception:

        pass


def log_success(
    request,
    action,
    result=""
):

    try:

        record_success(
            request,
            action,
            result
        )

    except Exception:

        pass