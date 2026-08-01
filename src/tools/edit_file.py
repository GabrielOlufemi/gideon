from tools.pathsafe import BASE_PATH, is_safe_path

EDIT_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Replaces an exact snippet of text in an existing file with new text. "
            "old_string must match the file's content exactly (including whitespace) "
            "and must be unique within the file — include enough surrounding context "
            "to guarantee that. Use this for targeted changes instead of write_file, "
            "which would destroy the rest of the file's content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact, unique text to find and replace"
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace old_string with"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "If true, replace every occurrence instead of requiring old_string to be unique. Defaults to false."
                }
            },
            "required": ["path", "old_string", "new_string"]
        }
    }
}


def edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"

    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_file():
        return f"Error: {path} is not a file"

    if old_string == new_string:
        return "Error: old_string and new_string are identical, nothing to change"

    try:
        content = target.read_text()
    except Exception as e:
        return f"Error reading '{path}': {e}"

    count = content.count(old_string)

    if count == 0:
        return f"Error: old_string not found in '{path}'"

    if count > 1 and not replace_all:
        return (
            f"Error: old_string appears {count} times in '{path}', "
            "not unique. Add more surrounding context, or pass replace_all=true"
        )

    new_content = content.replace(old_string, new_string, -1 if replace_all else 1)

    try:
        target.write_text(new_content)
    except Exception as e:
        return f"Error writing to '{path}': {e}"

    return f"Successfully edited '{path}'"
