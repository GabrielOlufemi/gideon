import subprocess
from pathlib import Path
from tools.pathsafe import BASE_PATH

BASH_TIMEOUT_SECONDS = 120

RUN_BASH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_bash",
        "description": (
            "Run a shell command in the project's root directory and return its "
            "exit code, stdout, and stderr. Use this for things read_file, "
            "write_file, and list_directories can't do — running tests, installing "
            "packages, checking git status, running scripts, and similar tasks. "
            "This command always requires the user's explicit approval before it "
            "runs, so prefer the more targeted file tools when they're sufficient."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "A single shell command line to execute, exactly as you'd "
                        "type it in a terminal (e.g. 'pytest', 'git status', "
                        "'pip install requests'). Multiple commands can be chained "
                        "with '&&' or ';'."
                    )
                },
                "description": {
                    "type": "string",
                    "description": (
                        "A very brief 1-2 sentence explanation of what this "
                        "command does and why it's being run. Helps the user "
                        "understand what they're approving."
                    )
                }
            },
            "required": ["command", "description"]
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