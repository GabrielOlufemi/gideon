import re
import subprocess
import sys
from pathlib import Path
from gideon.tools.pathsafe import BASE_PATH, is_safe_path, should_exclude, EXCLUDED_DIRS

MAX_RESULTS = 200

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


def _native_grep(pattern: str, target: Path, case_sensitive: bool) -> str | None:
    """Try native grep. Returns result string or None if grep isn't available."""
    if sys.platform == "win32":
        return None  # No native grep on Windows

    # Build exclusion args — --exclude-dir for each excluded dir
    exclude_args = []
    for d in EXCLUDED_DIRS:
        exclude_args.extend(["--exclude-dir", d])

    flags = ["-rn", "--max-count", "1"]
    if not case_sensitive:
        flags.append("-i")

    # Use -E for extended regex, -F for fixed-string if pattern has no regex metacharacters
    has_meta = bool(re.search(r"[.*+?^$(){}[\]|\\]", pattern))
    if not has_meta:
        flags.append("-F")

    cmd = ["grep"] + exclude_args + flags + [pattern, str(target)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, PermissionError):
        return None  # grep not available, fall back
    except subprocess.TimeoutExpired:
        return "Error: grep timed out after 30 seconds"

    if result.returncode not in (0, 1):
        return None  # grep itself errored — fall back

    output = result.stdout
    if not output.strip():
        return "No matches found"

    # Truncate and relativize paths
    lines = output.splitlines()
    truncated = len(lines) > MAX_RESULTS
    lines = lines[:MAX_RESULTS]

    # Grep outputs paths prefixed with the target argument (which is absolute).
    # Strip that prefix, then re-root to BASE_PATH-relative paths.
    target_prefix = str(target) + "/"
    subdir_offset = target.relative_to(BASE_PATH)
    subdir_str = str(subdir_offset) + "/" if str(subdir_offset) != "." else ""

    rel_lines = []
    for line in lines:
        if line.startswith(target_prefix):
            rel_path = line[len(target_prefix):]
        else:
            rel_path = line
        rel_lines.append(f"{subdir_str}{rel_path}")

    result_text = "\n".join(rel_lines)
    if truncated:
        result_text += f"\n... truncated, showing first {MAX_RESULTS} matches"

    return result_text


def _python_grep(pattern: str, target: Path, case_sensitive: bool) -> str:
    """Pure-Python fallback grep."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: invalid regex pattern: {e}"

    results: list[str] = []

    for entry in target.rglob("*"):
        if not entry.is_file():
            continue
        if should_exclude(entry):
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


def grep_search(pattern: str, path: str = ".", case_sensitive: bool = True) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_dir():
        return f"Error: {path} is not a directory"

    # Try native grep first (much faster), fall back to Python
    result = _native_grep(pattern, target, case_sensitive)
    if result is not None:
        return result

    return _python_grep(pattern, target, case_sensitive)