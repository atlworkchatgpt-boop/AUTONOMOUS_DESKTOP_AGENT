import os
import platform


def get_system_information():

    return {
        "platform": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "username": os.environ.get(
            "USERNAME",
            "unknown"
        )
    }


AVAILABLE_SYSTEM_TOOLS = {
    "get_system_information":
        get_system_information
}
