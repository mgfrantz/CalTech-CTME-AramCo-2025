from pathlib import Path
from dotenv import load_dotenv


def get_repo_root(max_depth: int = 5) -> Path:
    """
    Get the root directory of the repository.

    Args:
        max_depth (int): The maximum number of parent directories to search.

    Returns:
        Path: The root directory of the repository.
    """
    current_dir = Path.cwd()
    for _ in range(max_depth):
        if (current_dir / ".git").exists():
            return current_dir
        current_dir = current_dir.parent
    raise FileNotFoundError("Repository root not found")


def get_root_dotenv(load: bool = True) -> Path:
    """
    Get the root directory of the repository and return the path to the .env file
    
    Args:
        load (bool): Whether to load the .env file into the environment variables.

    Returns:
        Path: The path to the .env file.
    """
    env_path = get_repo_root() / ".env"
    if load:
        loaded = load_dotenv(env_path, override=True)
        if not loaded:
            raise FileNotFoundError("Failed to load .env file")
    return env_path
