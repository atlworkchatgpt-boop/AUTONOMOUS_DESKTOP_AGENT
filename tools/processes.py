import psutil


def processes():

    rows = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "memory_percent",
        ]
    ):

        try:

            rows.append(
                {
                    "pid": process.info["pid"],
                    "name": process.info["name"],
                    "memory_percent": process.info[
                        "memory_percent"
                    ],
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            continue

    return {
        "ok": True,
        "processes": rows[:250],
    }