import platform

import psutil


def system_info():

    memory = psutil.virtual_memory()

    return {
        "ok": True,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cpu_percent": psutil.cpu_percent(
            interval=0.2
        ),
        "memory_percent": memory.percent,
        "memory_gb": round(
            memory.total / (1024 ** 3),
            2,
        ),
    }


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