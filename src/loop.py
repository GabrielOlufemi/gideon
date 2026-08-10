import json
import difflib
from openrouter import chat_stream
from config import load_config

# scaffolding stuff
from pathlib import Path
from session_manager import save_session, list_sessions, new_session_path, load_session

# normal config imports
from config import get_agent_name

# color config imports 
from display import (
    print_error, stream_token,
    print_tool, print_permission, print_user,
    print_top_rule, print_info, print_success, console
)

from picker import select_choice
from exceptions import PickerCancelled
import questionary

# tool + model related stuff
from tools.read_file import read_file
from tools.write_file import write_file
from tools.list_directories import list_directories
from tools.run_bash import run_bash
from tools.edit_file import edit_file
from tools.grep_search import grep_search
from tools_config import get_model, TOOLS, DESTRUCTIVE_TOOLS

from tools.pathsafe import BASE_PATH
from rich.syntax import Syntax
from system_prompt import build_system_prompt

# commands stuff
from commands.settings import open_settings

ALWAYS_ALLOWED = []

# terminate words
TERMINATE_KEYWORDS = ["quit", "exit", "leave"]
CONSOLE_COMMANDS = ["/settings", "/sessions", "/restore"]

# stores conversation history per session
# context = [] -> moved ts to main.py

# tool exec logic
def run_tool(call):
    name = call["function"]["name"]

    try:
        arguments = json.loads(call["function"]["arguments"])
    except json.JSONDecodeError as e:
        return f"Error: malformed arguments for '{name}' : {e}"

    if name in DESTRUCTIVE_TOOLS and name not in ALWAYS_ALLOWED:
        decision = request_permission(name, arguments)

        if decision == "no":
            return f"Permission denied by user for '{name}'"
        
        if decision == "always":
            ALWAYS_ALLOWED.append(name)


    if name == "read_file":
        # tool call print
        print_tool(f"Reading {arguments["path"]}...")
        return read_file(arguments["path"])


    if name == "write_file":
        print_tool(f"Writing to {arguments["path"]}...")
        return write_file(arguments["path"], arguments["content"])


    if name == "list_directories":
        print_tool(f"Listing {arguments["dir_path"]}...")
        return list_directories(arguments["dir_path"])
    
    if name == "run_bash":
        print_tool(f"Executing command:  {arguments["command"]}")
        return run_bash(arguments["command"])

    if name == "edit_file":
        print_tool(f"Editing {arguments["path"]}...")
        return edit_file(
            arguments["path"],
            arguments["old_string"],
            arguments["new_string"],
            arguments.get("replace_all", False)
        )

    if name == "grep_search":
        print_tool(f"Searching for: {arguments["pattern"]}...")
        return grep_search(
            arguments["pattern"],
            arguments.get("path", "."),
            arguments.get("case_sensitive", True)
        )

    return f"Error: unknown tool '{name}'"


# diff generation for permission prompts
def _generate_write_diff(path: str, new_content: str) -> str | None:
    target = (BASE_PATH / path).resolve()

    try:
        old = target.read_text() if target.exists() else ""
    except Exception:
        return None

    old_lines = old.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    fromfile = "/dev/null" if not target.exists() else path

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=fromfile, tofile=path,
        n=3
    )

    return "".join(diff)


def _generate_edit_diff(path: str, old_string: str, new_string: str) -> str | None:
    target = (BASE_PATH / path).resolve()

    if not target.exists():
        return None

    try:
        original = target.read_text()
    except Exception:
        return None

    if old_string not in original:
        return None

    modified = original.replace(old_string, new_string, 1)

    old_lines = original.splitlines(keepends=True)
    new_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=path, tofile=path,
        n=3
    )

    return "".join(diff)


# permission request logic
def request_permission(name: str, arguments: dict[str, str]) -> str:

    # individual check for existing tools
    if name == "write_file":
        details = f"path: {arguments.get('path')}"
        diff = _generate_write_diff(arguments["path"], arguments["content"])
        if diff:
            console.print()
            console.print(Syntax(diff, "diff", line_numbers=False))
    elif name == "edit_file":
        details = f"path: {arguments.get('path')}"
        diff = _generate_edit_diff(arguments["path"], arguments["old_string"], arguments["new_string"])
        if diff:
            console.print()
            console.print(Syntax(diff, "diff", line_numbers=False))
    elif name == "run_bash":
        details = f"command: {arguments.get('command')}"
    else:
        details = f"arguments: {arguments}"

    allow_always = name != "run_bash"

    if allow_always:
        choices = [
            questionary.Choice(title="Allow once", value="yes"),
            questionary.Choice(title="Always allow", value="always"),
            questionary.Choice(title="Deny", value="no"),
        ]
    else:
        choices = [
            questionary.Choice(title="Allow once", value="yes"),
            questionary.Choice(title="Deny", value="no"),
        ]

    print_permission(name, details)

    try:
        return select_choice("Choose an action:", choices)
    except PickerCancelled:
        print_error("Cancelled, denying by default")
        return "no"

def run_loop(context: list[dict], session_path: Path, session_dir: Path) -> None:
    model = get_model()
    api_key = load_config()["openrouter_api_key"]


    while True:

        print_top_rule()
        user_input = input("> ")
        print_user(user_input)

        # check if input is a console command
        cmd_parts = user_input.strip().split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""

        if cmd in TERMINATE_KEYWORDS:
            break

        if cmd in CONSOLE_COMMANDS:

            if cmd == "/settings":
                open_settings()
                continue

            if cmd == "/sessions":
                sessions = list_sessions(session_dir)
                if not sessions:
                    print_info(["No sessions for this project."])
                else:
                    lines = []
                    for i, s in enumerate(sessions, start=1):
                        lines.append(f"{i}. {s['display']}")
                    print_info(lines)
                continue

            if cmd == "/restore":
                if len(cmd_parts) < 2:
                    print_error("Usage: /restore <session_number>")
                    continue
                try:
                    session_num = int(cmd_parts[1])
                except ValueError:
                    print_error("Usage: /restore <session_number>")
                    continue

                sessions = list_sessions(session_dir)
                if session_num < 1 or session_num > len(sessions):
                    print_error(f"Session {session_num} not found. Use /sessions to list them.")
                    continue

                target = sessions[session_num - 1]
                context = load_session(target["path"])
                session_path = new_session_path(session_dir)
                print_success(f"Restored from {target['display']} in a new session.")
                continue

 
        # check if input is empty
        if user_input.strip().lower() == "":
            # error print
            print_error("Type in something big dawg")
            continue

        # start of a turn
        try:
            context.append({
                "role":"user", "content":user_input
            })

            while True:
                system_message = {"role": "system", "content": build_system_prompt(get_agent_name(), TOOLS, DESTRUCTIVE_TOOLS)}
                stream = chat_stream([system_message] + context, model, api_key, TOOLS)

                final_message = None
                streamed_content = False

                for chunk in stream:
                    if isinstance(chunk, str):
                        if not streamed_content:
                            streamed_content = True
                            stream_token("   ")
                        stream_token(chunk)
                    else:
                        final_message = chunk
                        if streamed_content:
                            print()

                if final_message is None:
                    break

                if final_message.get("tool_calls"):
                    context.append(final_message)

                    for call in final_message["tool_calls"]:
                        try:
                            result = run_tool(call)
                            print_tool(f"Done.")
                            context.append({
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": result
                            })
                        except Exception as e:
                            context.append({
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": f"Error: {e}"
                            })

                    continue

                reply_text = final_message.get("content") or ""

                context.append({
                    "role":"assistant", "content":reply_text
                })

                # saving turn to session log
                save_session(session_path, context)

                break

        except Exception as e:
            # error print
            print_error(f"Error: {e}")
            continue