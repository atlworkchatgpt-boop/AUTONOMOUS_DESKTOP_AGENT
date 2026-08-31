import os
import sys
import runpy

from agent.computer_control import require_startup_password


if __name__ == "__main__":

    if not require_startup_password():

        input("\nPress Enter to exit...")

        raise SystemExit(1)

    dashboard = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "dashboard.py"
    )

    runpy.run_path(
        dashboard,
        run_name="__main__"
    )
