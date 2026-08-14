from gideon.tools.pathsafe import BASE_PATH, is_safe_path


READ_FILE_RANGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file_range",
        "description": "Read a specific range of lines from a file. Useful for examining parts "
            "of a file without reading its entire contents, saving tokens and context space. "
            "Line numbers are 1-indexed. Omitting end_line reads to the end of the file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "First line to read (1-indexed). Defaults to 1."
                },
                "end_line": {
                    "type": "integer",
                    "description": "Last line to read (inclusive). If omitted, reads to end of file."
                }
            },
            "required": ["path"]
        }
    }
}


def read_file_range(path: str, start_line: int = 1, end_line: int | None = None) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_file():
        return f"Error: {path} is not a file"

    try:
        lines = target.read_text().splitlines()
    except Exception as e:
        return f"Error reading '{path}': {e}"

    total_lines = len(lines)

    if start_line < 1:
        return f"Error: start_line must be >= 1, got {start_line}"

    if start_line > total_lines:
        return f"Error: start_line ({start_line}) exceeds file length ({total_lines} lines)"

    if end_line is not None:
        if end_line < start_line:
            return f"Error: end_line ({end_line}) must be >= start_line ({start_line})"
        if end_line > total_lines:
            end_line = total_lines
    else:
        end_line = total_lines

    selected = lines[start_line - 1 : end_line]

    result_lines = []
    for i, line in enumerate(selected, start=start_line):
        result_lines.append(f"{i:>6}: {line}")

    header = f"{path} (lines {start_line}-{end_line} of {total_lines})"
    return header + "\n" + "\n".join(result_lines)