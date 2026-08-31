import subprocess

from config.config import MAX_OUTPUT_CHARS


def run_command(command, cwd=None, timeout=60):

    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = (
            (completed.stdout or "")
            + (completed.stderr or "")
        )

        output = output[-MAX_OUTPUT_CHARS:]

        return completed.returncode, output.strip()

    except subprocess.TimeoutExpired:
        return -1, "Command timed out."

    except Exception as exc:
        return -1, f"Command error: {exc}"
