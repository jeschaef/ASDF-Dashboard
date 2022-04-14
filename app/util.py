import os
from pathlib import Path


def ensure_exists_folder(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as err:
            print(f"OSERROR: {err}")


def get_project_root() -> Path:
    """Return the path of the project root folder.

    Returns:
        Path: Path to project root
    """
    return Path(__file__).parent