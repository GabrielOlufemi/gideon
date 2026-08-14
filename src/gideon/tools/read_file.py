from gideon.tools.pathsafe import BASE_PATH, is_safe_path

READ_FILE_SCHEMA = {
    "type" : "function",
    "function" : {
        "name" : "read_file",
        "description" : "Reads the full text content of a specific file. Use this once you know the exact path to a file — for example after list_directories has revealed it — rather than guessing a path that hasn't been confirmed to exist.",
        "parameters" : {
            "type" : "object",
            "properties" : {
                "path" : {
                    "type" : "string",
                    "description" : "Relative or absolute path to file to read"
                }
            },
            "required" : ["path"]
        }
    }
}


def read_file(path: str) -> str:
    if not is_safe_path(path):
        return f"Error, {path} is outside of the allowed project directory"
    
    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return f"Error: {path} does not exist"

    if not target.is_file():
        return f"Error: {path} is not a file"

    try:
        return target.read_text()
    except Exception as e:
        return f"Error reading '{path}' : {e}"