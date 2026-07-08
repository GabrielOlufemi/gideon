from pathlib import Path
from tools.pathsafe import BASE_PATH, is_safe_path

LIST_DIRECTORIES_SCHEMA = {
    "type" : "function",
    "function" : {
        "name" : "list_directories",
        "description" : "Lists the files and subdirectories one level deep inside the given directory. Use it to explore the project structure incrementally — start at the root, then call again with a subdirectory's path to look inside it, rather than assuming what it contains.",
        "parameters" : {
            "type" : "object",
            "properties" : {
                "dir_path" : {
                    "type":"string",
                    "description" : "Relative or absolute path of the directory to list"
                }
            },
            "required" : ["dir_path"]
        }
    }
} 


def list_directories(dir_path: str) -> str:
    if not is_safe_path(dir_path):
        return f"Error, {dir_path} is outside of the allowed project directory"
    
    target = (BASE_PATH / dir_path).resolve()

    if not target.exists():
        return f"Error: {dir_path} does not exist"
    
    if not target.is_dir():
        return f"Error: {dir_path} is not a directory"
    
    try:

        dirs = []
        files = []

        for entry in target.iterdir():
            if entry.is_dir():
                dirs.append(entry.relative_to(BASE_PATH))
            else:
                files.append(entry.relative_to(BASE_PATH))

        dirs.sort()
        files.sort()

        lines = [f"{d}/ (directory)" for d in dirs] + [f"{f} (file)" for f in files]

        return "\n".join(lines) if lines else "empty(directory)"

    except Exception as e:
        return f"Error listing '{dir_path}' : {e}"