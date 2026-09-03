
from pathlib import Path
import shutil


def create_folder(path):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def list_files(path):
    p = Path(path)

    if not p.exists():
        return []

    return [
        {
            "name": x.name,
            "path": str(x),
            "is_directory": x.is_dir()
        }
        for x in p.iterdir()
    ]


def copy_file(source, destination):
    src = Path(source)
    dst = Path(destination)

    dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, dst)

    return str(dst)


def move_file(source, destination):
    src = Path(source)
    dst = Path(destination)

    dst.parent.mkdir(parents=True, exist_ok=True)

    return str(shutil.move(str(src), str(dst)))


def rename_file(source, new_name):
    src = Path(source)
    dst = src.with_name(new_name)

    src.rename(dst)

    return str(dst)


def delete_file(path):
    p = Path(path)

    if p.is_file():
        p.unlink()
        return True

    if p.is_dir():
        shutil.rmtree(p)
        return True

    return False
