from pathlib import Path


def list_directory(
    path,
):

    p = Path(
        path
    ).expanduser().resolve()

    if not p.exists():

        return {
            "ok": False,
            "error": (
                f"Directory does not exist: {p}"
            ),
        }

    if not p.is_dir():

        return {
            "ok": False,
            "error": (
                f"Not a directory: {p}"
            ),
        }

    rows = []

    try:

        for item in sorted(
            p.iterdir(),
            key=lambda x: (
                not x.is_dir(),
                x.name.lower(),
            ),
        ):

            rows.append(
                {
                    "name": item.name,
                    "type": (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),
                    "path": str(item),
                }
            )

        return {
            "ok": True,
            "path": str(p),
            "items": rows,
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
        }


def read_file(
    path,
    max_chars=30000,
):

    p = Path(
        path
    ).expanduser().resolve()

    if not p.is_file():

        return {
            "ok": False,
            "error": f"File not found: {p}",
        }

    try:

        return {
            "ok": True,
            "path": str(p),
            "content": p.read_text(
                encoding="utf-8",
                errors="replace",
            )[:max_chars],
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
        }


def write_file(
    path,
    content,
):

    p = Path(
        path
    ).expanduser().resolve()

    try:

        p.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        p.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "ok": True,
            "path": str(p),
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
        }