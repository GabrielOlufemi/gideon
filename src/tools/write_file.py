from tools.pathsafe import BASE_PATH, is_safe_path


WRITE_FILE_SCHEMA = {
    "type" : "function",
    "function" : {
        "name" : "write_file",
        "description" : "Create a new file or completely replace the contents of an existing "
            "file at the given path. This is a full overwrite, not an append or "
            "merge — any existing content in the file is destroyed and replaced "
            "entirely with the new content. Use this when creating a new file from "
            "scratch, or when you intend to replace a file's entire contents. Do "
            "not use this to make a small change to part of an existing file — "
            "that requires reading the file first and reconstructing its full "
            "intended content before calling this.",
        "parameters" : {
            "type" : "object",
            "properties" : {
                "path" : {
                    "type" : "string",
                    "description" : "The path to the file to create or overwrite, relative to the project root."
                }, 
                "content" : {
                    "type" : "string",
                    "description" : "The full content the file should contain after this call."
                }
            },
            "required" : ["path", "content"]
        }
    }
} 

def write_file(path: str, content: str) -> str:
    if not is_safe_path(path):
        return f"Error: '{path}' is outside the allowed directory"
    
    target = (BASE_PATH / path).resolve()

    if target.exists() and target.is_dir():
        return f"Error: '{path}' is a directory, cannot write to it"
    

    try:
        target.write_text(content)
    except Exception as e:
        return f"Error writing to '{path}' : {e}"
    
    return f"Successfully wrote to '{path}'"