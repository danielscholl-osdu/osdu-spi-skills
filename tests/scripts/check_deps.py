# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///
"""Compatibility shim for the dependency checker.

The runtime checker moved from tests/scripts to skills/setup/scripts.
This file is kept temporarily to avoid breaking existing local commands.
"""

from pathlib import Path
import runpy


def main() -> None:
    target = (
        Path(__file__).resolve().parent.parent.parent
        / "skills"
        / "setup"
        / "scripts"
        / "check_deps.py"
    )
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
