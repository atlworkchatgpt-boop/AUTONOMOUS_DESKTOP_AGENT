import os
import sys

PROJECT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from desktop_app import main

if __name__ == "__main__":
    main()
