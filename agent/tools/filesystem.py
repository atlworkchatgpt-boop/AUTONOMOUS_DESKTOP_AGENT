import os


def list_directory(path="."):

    try:

        path = os.path.abspath(path)

        if not os.path.isdir(path):
            return {
                "success": False,
                "error": "Directory does not exist."
            }

        items = []

        for name in os.listdir(path):

            full = os.path.join(path, name)

            items.append({
                "name": name,
                "type": "directory"
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


def read_text_file(path):

    try:

        path = os.path.abspath(path)

        if not os.path.isfile(path):
            return {
                "success": False,
                "error": "File does not exist."
            }

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as f:

            content = f.read()

        return {
            "success": True,
            "path": path,
            "content": content
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


def create_text_file(path, content):

    try:

        path = os.path.abspath(path)

        parent = os.path.dirname(path)

        if parent:
            os.makedirs(
                parent,
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


TOOLS = {
    "list_directory": list_directory,
    "read_text_file": read_text_file,
    "create_text_file": create_text_file
}
