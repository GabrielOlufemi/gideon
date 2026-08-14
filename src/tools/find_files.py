from pathlib import Path
from tools.pathsafe import BASE_PATH, is_safe_path


FIND_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "find_files",
        "description": "Recursively find files matching a glob pattern. Use this to locate files "
            "by name or extension when you don't know their exact path. Supports wildcards like "
            "'*.py', '**/test_*.py', '*config*', etc. Does not search inside .git, .venv, "
            "node_modules, and similar excluded directories.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match against file names, relative to the search path"
                },
                "path": {
                    "type": "string",
                    "description": "Root directory to search in. Defaults to project root if omitted."
                }
            },
            "required": ["pattern"]
        }
    }
}

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}


def _should_exclude(entry: Path) -> bool:
    for part in entry.relative_to(BASE_PATH).parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def find_files(pattern: str, path: str = ".") -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_dir():
        return f"Error: {path} is not a directory"

    try:
        matches = []
        for entry in target.rglob(pattern):
            if not entry.is_file():
                continue
            if _should_exclude(entry):
                continue
            rel_path = entry.relative_to(BASE_PATH)
            matches.append(str(rel_path))

        matches.sort()

        if not matches:
            return f"No files matching '{pattern}' found in '{path}'"

        return "\n".join(matches)

    except Exception as e:
        return f"Error searching for '{pattern}' in '{path}': {e}"