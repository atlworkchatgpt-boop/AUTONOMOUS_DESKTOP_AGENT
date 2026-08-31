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


TOOLS = {
    "open_application": open_application,
    "open_url": open_url
}
