from pathlib import Path

BASE_PATH = Path.cwd().resolve()

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def is_safe_path(path: str) -> bool:
    candidate = (BASE_PATH / path).resolve()
    return candidate.is_relative_to(BASE_PATH)


def should_exclude(entry: Path) -> bool:
    """Check if any component of the path is in the excluded dirs list."""
    for part in entry.relative_to(BASE_PATH).parts:
        if part in EXCLUDED_DIRS:
            return True
    return False