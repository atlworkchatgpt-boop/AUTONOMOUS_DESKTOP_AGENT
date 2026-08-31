import os
import shutil
import subprocess
import webbrowser
from agent.config import PASSWORD


def protected(action):

    print()
    print("================================================")
    print(" PROTECTED COMPUTER ACTION")
    print(" Action:", action)
    print("================================================")

    entered = input(
        "Enter password: "
    )

    return entered == PASSWORD


def list_directory(path="."):

    path = os.path.abspath(path)

    if not os.path.isdir(path):
        return {
            "success": False,
            "error": "Directory not found: " + path
        }

    items = []

    try:

        for name in os.listdir(path):

            full = os.path.join(
                path,
                name
            )

            items.append({
                "name": name,
                "type":
                    "folder"
                    if os.path.isdir(full)
                    else "file"
            })

        return {
            "success": True,
            "path": path,
            "items": items
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def read_file(path):

    path = os.path.abspath(path)

    if not os.path.isfile(path):
        return {
            "success": False,
            "error": "File not found."
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as f:

            text = f.read()

        return {
            "success": True,
            "path": path,
            "content": text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def create_file(path, content):

    if not protected(
        "CREATE FILE: " + path
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    path = os.path.abspath(path)

    try:

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        return {
            "success": True,
            "path": path
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def delete_file(path):

    if not protected(
        "DELETE: " + path
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    path = os.path.abspath(path)

    try:

        if os.path.isfile(path):
            os.remove(path)

        elif os.path.isdir(path):
            shutil.rmtree(path)

        else:
            return {
                "success": False,
                "error": "Path not found."
            }

        return {
            "success": True,
            "path": path
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def open_url(url):

    if not protected(
        "OPEN BROWSER: " + url
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    try:

        webbrowser.open(url)

        return {
            "success": True,
            "url": url
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def open_application(command):

    if not protected(
        "OPEN APPLICATION: " + command
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    try:

        subprocess.Popen(
            command,
            shell=True
        )

        return {
            "success": True,
            "command": command
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def close_application(process_name):

    if not protected(
        "CLOSE APPLICATION: " + process_name
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    try:

        result = subprocess.run(
            [
                "taskkill",
                "/IM",
                process_name,
                "/F"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error":
                    result.stderr.strip()
                    or result.stdout.strip()
            }

        return {
            "success": True,
            "process": process_name
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def install_program(command):

    if not protected(
        "INSTALL: " + command
    ):
        return {
            "success": False,
            "error": "Password rejected."
        }

    try:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "success":
                result.returncode == 0,
            "returncode":
                result.returncode,
            "stdout":
                result.stdout[-4000:],
            "stderr":
                result.stderr[-4000:]
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


TOOLS = {
    "list_directory": list_directory,
    "read_file": read_file,
    "create_file": create_file,
    "delete_file": delete_file,
    "open_url": open_url,
    "open_application": open_application,
    "close_application": close_application,
    "install_program": install_program
}
