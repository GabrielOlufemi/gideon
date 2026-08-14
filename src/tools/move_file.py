import shutil
from tools.pathsafe import BASE_PATH, is_safe_path


MOVE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "move_file",
        "description": "Move or rename a file or directory. Can move files between directories, "
            "rename them in place, or both at once. Uses shutil.move under the hood. "
            "Destination must not already exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Current path of the file or directory to move"
                },
                "destination": {
                    "type": "string",
                    "description": "Target path to move or rename to"
                }
            },
            "required": ["source", "destination"]
        }
    }
}


def move_file(source: str, destination: str) -> str:
    if not is_safe_path(source):
        return f"Error: source '{source}' is outside the allowed directory"

    if not is_safe_path(destination):
        return f"Error: destination '{destination}' is outside the allowed directory"

    src_path = (BASE_PATH / source).resolve()
    dst_path = (BASE_PATH / destination).resolve()

    if not src_path.exists():
        return f"Error: source '{source}' does not exist"

    if dst_path.exists():
        return f"Error: destination '{destination}' already exists"

    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating parent directory for '{destination}': {e}"

    try:
        shutil.move(str(src_path), str(dst_path))
    except Exception as e:
        return f"Error moving '{source}' to '{destination}': {e}"

    return f"Successfully moved '{source}' to '{destination}'"