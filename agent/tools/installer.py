import subprocess
from security.security import require_password


def install_package(package):

    if not require_password(
        f"INSTALL SOFTWARE: {package}"
    ):
        return {
            "success": False,
            "error": "Password verification failed."
        }

    try:

        result = subprocess.run(
            [
                "winget",
                "install",
                "--id",
                package,
                "--accept-source-agreements",
                "--accept-package-agreements"
            ],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "package": package,
            "returncode": result.returncode,
            "output": result.stdout[-4000:],
            "error": result.stderr[-2000:]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


AVAILABLE_INSTALL_TOOLS = {
    "install_package": install_package
}
