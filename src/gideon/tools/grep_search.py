import re
from pathlib import Path
from gideon.tools.pathsafe import BASE_PATH, is_safe_path

MAX_RESULTS = 200

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}

GREP_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "grep_search",
        "description": (
            "Searches file contents across the project for a pattern using grep, and "
            "returns matching lines with their file path and line number. Use this to "
            "find where something is defined or used across the whole codebase in one "
            "call, instead of guessing which file to open with list_directories and "
            "read_file. Supports extended regular expressions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The text or extended regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Relative directory to search within. Defaults to the project root if omitted."
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether the search is case-sensitive. Defaults to true."
                }
            },
            "required": ["pattern"]
        }
    }
}


def _should_exclude(entry: Path) -> bool:
    """Check if any component of the path is in the excluded dirs list."""
    for part in entry.relative_to(BASE_PATH).parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def grep_search(pattern: str, path: str = ".", case_sensitive: bool = True) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_dir():
        return f"Error: {path} is not a directory"

    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: invalid regex pattern: {e}"

    results: list[str] = []

    for entry in target.rglob("*"):
        if not entry.is_file():
            continue
        if _should_exclude(entry):
            continue

        try:
            text = entry.read_text(errors="replace")
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                rel_path = entry.relative_to(BASE_PATH)
                results.append(f"{rel_path}:{lineno}:{line}")

                if len(results) >= MAX_RESULTS:
                    break

        if len(results) >= MAX_RESULTS:
            break

    if not results:
        return "No matches found"

    output = "\n".join(results)

    if len(results) >= MAX_RESULTS:
        output += f"\n... truncated, showing first {MAX_RESULTS} matches"

    return output