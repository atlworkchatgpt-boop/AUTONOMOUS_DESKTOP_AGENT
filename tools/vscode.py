from tools.terminal import run_command


def open_vscode(path=None):

    command = "code"

    if path:
        command += f' "{path}"'

    return run_command(
        command,
        timeout=20,
    )
