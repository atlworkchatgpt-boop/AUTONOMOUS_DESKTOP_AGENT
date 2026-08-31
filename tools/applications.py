import os
import subprocess


def open_application(command):

    try:
        subprocess.Popen(
            command,
            shell=True,
        )

        return True, (
            f"Started: {command}"
        )

    except Exception as exc:
        return False, str(exc)


def open_folder(path):

    try:
        os.startfile(
            os.path.abspath(path)
        )

        return True, (
            f"Opened folder: {path}"
        )

    except Exception as exc:
        return False, str(exc)
