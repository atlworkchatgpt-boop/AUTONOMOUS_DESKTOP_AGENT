import os
import subprocess
import webbrowser


def open_application(command):

    try:

        subprocess.Popen(
            command,
            shell=True
        )

        return {
            "success": True,
            "message":
            "Application launch command executed.",
            "command": command
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def open_url(url):

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


def list_directory(path="."):

    try:

        path = os.path.abspath(path)

        if not os.path.isdir(path):

            return {
                "success": False,
                "error":
                "Directory does not exist."
            }

        result = []

        for name in os.listdir(path):

            full = os.path.join(
                path,
                name
            )

            result.append({
                "name": name,
                "type":
                "folder"
                if os.path.isdir(full)
                else "file"
            })

        return {
            "success": True,
            "path": path,
            "items": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def read_text_file(path):

    try:

        path = os.path.abspath(path)

        if not os.path.isfile(path):

            return {
                "success": False,
                "error":
                "File does not exist."
            }

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
