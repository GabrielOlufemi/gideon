from pathlib import Path

BASE_PATH = Path.cwd().resolve()

def is_safe_path(path: str) -> bool:
    candidate = (BASE_PATH / path).resolve()

    return candidate.is_relative_to(BASE_PATH)