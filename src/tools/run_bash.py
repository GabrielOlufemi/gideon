import subprocess
from pathlib import Path
from tools.pathsafe import BASE_PATH

BASH_TIMEOUT_SECONDS = 120

RUN_BASH_SCHEMA = {
    "type" :  "function",
    "function" : {
        "name" : "run_bash",
        "description" : "Execute bash commands in the users terminal",
        "parameters" : {
            "type" : "object",
            "properties" : {
                "command" : {
                    "type" : "string",
                    "description" : "string of commands required for execution"
                }
            },
            "required" : ["command"]
        }
    }
}


def run_bash(command: str) -> str:

    try:
        result = subprocess.run(
            command,
            shell = True,
            cwd=BASE_PATH,
            capture_output=True,
            text=True,
            timeout=BASH_TIMEOUT_SECONDS,
        )

    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {BASH_TIMEOUT_SECONDS} seconds: {command}"
    except Exception as e:
        return f"Error running '{command}': {e}"
    
    return(
        f"exit code: {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )