from pathlib import Path


def get_project_root() -> Path:
    """Return the path of the project root folder.

    Returns:
        Path: Path to project root
    """
    return Path(__file__).parent