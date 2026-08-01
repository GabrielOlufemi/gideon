import subprocess
from pathlib import Path
from tools.pathsafe import BASE_PATH, is_safe_path

MAX_RESULTS = 200

EXCLUDED_DIRS = [".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"]

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


def grep_search(pattern: str, path: str = ".", case_sensitive: bool = True) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_dir():
        return f"Error: {path} is not a directory"

    command = ["grep", "-r", "-n", "-I", "-E"]

    if not case_sensitive:
        command.append("-i")

    for excluded in EXCLUDED_DIRS:
        command.append(f"--exclude-dir={excluded}")

    command.append(pattern)
    command.append(str(target))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return "Error: grep is not installed on this system"
    except subprocess.TimeoutExpired:
        return "Error: search timed out"
    except Exception as e:
        return f"Error running search: {e}"

    if result.returncode not in (0, 1):
        return f"Error: grep failed: {result.stderr.strip()}"

    if result.returncode == 1:
        return "No matches found"

    lines = result.stdout.splitlines()

    truncated = len(lines) > MAX_RESULTS
    lines = lines[:MAX_RESULTS]

    output_lines = []
    for line in lines:
        try:
            abs_path, rest = line.split(":", 1)
            rel_path = Path(abs_path).relative_to(BASE_PATH)
            output_lines.append(f"{rel_path}:{rest}")
        except ValueError:
            output_lines.append(line)

    output = "\n".join(output_lines)

    if truncated:
        output += f"\n... truncated, showing first {MAX_RESULTS} matches"

    return output
