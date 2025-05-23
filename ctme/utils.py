"""
ctme.utils

Utility functions for repository path discovery and environment variable loading.

Functions:
    get_repo_root(max_depth=5):
        Returns the root directory of the repository by searching for a .git folder.
    get_root_dotenv(load=True):
        Returns the path to the .env file at the repository root and optionally loads it into environment variables.
"""
from pathlib import Path
from dotenv import load_dotenv


def get_repo_root(max_depth: int = 5) -> Path:
    """
    Search for the root directory of the repository by looking for a .git folder.

    Args:
        max_depth (int): The maximum number of parent directories to search upward from the current working directory.

    Returns:
        Path: The root directory of the repository.

    Raises:
        FileNotFoundError: If the repository root is not found within the specified depth.
    """
    current_dir = Path.cwd()
    for _ in range(max_depth):
        if (current_dir / ".git").exists():
            return current_dir
        current_dir = current_dir.parent
    raise FileNotFoundError("Repository root not found")


def get_root_dotenv(load: bool = True) -> Path:
    """
    Get the path to the .env file at the repository root and optionally load it into environment variables.

    Args:
        load (bool): If True, load the .env file into environment variables using dotenv.

    Returns:
        Path: The path to the .env file at the repository root.

    Raises:
        FileNotFoundError: If the .env file cannot be loaded when load=True.
    """
    env_path = get_repo_root() / ".env"
    if load:
        loaded = load_dotenv(env_path, override=True)
        if not loaded:
            raise FileNotFoundError("Failed to load .env file")
    return env_path
