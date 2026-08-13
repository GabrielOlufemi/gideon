import json
from openrouter import chat_stream
from config import load_config

# scaffolding stuff
from pathlib import Path
from session_manager import save_session, list_sessions, new_session_path, load_session, delete_session

# normal config imports
from config import get_agent_name

# color config imports 
from display import (
    print_error, StreamDisplay, print_edit_diff, print_write_summary, print_context_bar,
    print_tool, print_tool_summary, print_permission, print_user,
    print_top_rule, print_info, print_success, console, COLORS
)

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
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
from system_prompt import build_system_prompt, build_reminder

# commands stuff
from commands.settings import open_settings

TERMINATE_KEYWORDS = ["quit", "exit", "leave"]
CONSOLE_COMMANDS = ["/commands", "/settings", "/sessions", "/restore", "/delete"]


def _line_count(text: str) -> int:
    """Count lines matching standard editor behavior (wc -l style)."""
    if not text:
        return 0
    return text.count("\n") + 1


COMMANDS_TEXT = """\
  [bold]/commands[/bold]                  View all commands
  [bold]/settings[/bold]                  Open settings menu
  [bold]/sessions[/bold]                  List all sessions for this project
  [bold]/restore[/bold] [dim]<number>[/dim]         Restore a previous session
  [bold]/delete[/bold] [dim]<number>[/dim]          Delete a session
  [bold]quit[/bold], [bold]exit[/bold], [bold]leave[/bold]         End the session"""

# tool exec logic
def run_tool(call, always_allowed: list[str]):
    name = call["function"]["name"]

    try:
        arguments = json.loads(call["function"]["arguments"])
    except json.JSONDecodeError as e:
        return f"Error: malformed arguments for '{name}' : {e}"

    if name in DESTRUCTIVE_TOOLS and name not in always_allowed:
        decision = request_permission(name, arguments)
        if decision == "no":
            return f"Permission denied by user for '{name}'"
        if decision == "always":
            always_allowed.append(name)


    if name == "read_file":
        result = read_file(arguments["path"])
        line_count = _line_count(result) if result and not result.startswith("Error") else 0
        print_tool_summary("read_file", f"{arguments['path']} ({line_count} lines)")
        return result


    if name == "write_file":
        path = arguments["path"]
        content = arguments["content"]
        lines = _line_count(content)
        result = write_file(path, content)
        print_tool_summary("write_file", f"{path} ({lines} lines)")
        return result


    if name == "list_directories":
        result = list_directories(arguments["dir_path"])
        if result.startswith("Error"):
            print_tool_summary("list_directories", f"{arguments['dir_path']} — error")
        else:
            entries = [e for e in result.splitlines() if e != "empty(directory)"]
            print_tool_summary("list_directories", f"{arguments['dir_path']} ({len(entries)} entries)")
        return result

    if name == "run_bash":
        cmd = arguments["command"]
        desc = arguments.get("description")
        if desc:
            print_tool_summary("run_bash", f"{desc}")
        print_tool_summary("run_bash", cmd)
        result = run_bash(cmd)
        return result

    if name == "edit_file":
        path = arguments["path"]
        print_tool_summary("edit_file", path)
        old_string = arguments["old_string"]
        new_string = arguments["new_string"]
        replace_all = arguments.get("replace_all", False)

        # Capture old content before the edit for diff display
        old_content = _read_file_content(path)

        result = edit_file(path, old_string, new_string, replace_all)

        # Show diff after successful edit
        if result.startswith("Success") and old_content is not None:
            print_edit_diff(path, old_content, old_string, new_string)

        return result

    if name == "grep_search":
        print_tool_summary("grep_search", f"{arguments['pattern']}")
        result = grep_search(
            arguments["pattern"],
            arguments.get("path", "."),
            arguments.get("case_sensitive", True)
        )
        match_count = len(result.splitlines()) if result and not result.startswith("No") and not result.startswith("Error") else 0
        if match_count:
            print_tool_summary("grep_search", f"{match_count} matches")
        return result

    return f"Error: unknown tool '{name}'"


def _read_file_content(path: str) -> str | None:
    """Read a file's current content for diff display. Returns None if not found."""
    target = (BASE_PATH / path).resolve()
    try:
        return target.read_text() if target.exists() else None
    except Exception:
        return None


# permission request logic
def request_permission(name: str, arguments: dict[str, str]) -> str:

    # Show diff before the permission prompt
    if name == "write_file":
        path = arguments.get("path", "")
        old_content = _read_file_content(path)
        new_content = arguments.get("content", "")
        line_count = _line_count(new_content) if new_content else 0
        print_write_summary(path, old_content is not None, line_count)

    if name == "edit_file":
        path = arguments.get("path", "")
        old_string = arguments.get("old_string", "")
        new_string = arguments.get("new_string", "")
        old_content = _read_file_content(path)
        if old_content and old_string != new_string:
            print_edit_diff(path, old_content, old_string, new_string)

    if name == "write_file":
        details = f"path: {arguments.get('path')}"
    elif name == "edit_file":
        details = f"path: {arguments.get('path')}"
    elif name == "run_bash":
        desc = arguments.get("description")
        cmd = arguments.get("command", "")
        if desc:
            details = f"[dim]{desc}[/dim]\ncommand: {cmd}"
        else:
            details = f"command: {cmd}"
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
    always_allowed: list[str] = []

    # Build prompt_toolkit session with multiline keybinds
    kb = KeyBindings()

    @kb.add("enter")
    def _(event):
        """Enter submits the input."""
        event.current_buffer.validate_and_handle()

    @kb.add("escape", "enter")
    def _(event):
        """Alt+Enter inserts a newline (pasting multiline text also works natively)."""
        event.current_buffer.insert_text("\n")

    prompt_session = PromptSession(
        "> ",
        key_bindings=kb,
        multiline=True,
        history=None,
        enable_history_search=False,
        mouse_support=False,
    )

    while True:

        print_top_rule()

        try:
            user_input = prompt_session.prompt()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        # prompt_toolkit already displays the "> input" on screen —
        # just print a summary and the shortcut bar below it
        line_count = len(user_input.splitlines())
        if line_count > 1:
            console.print(f"   [Pasted +{line_count} lines]", style=COLORS["tool_detail"])
        console.print("   Alt+Enter for newline  |  Ctrl+C to interrupt", style=COLORS["tool_detail"])

        # check if input is a console command
        cmd_parts = user_input.strip().split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""

        if cmd in TERMINATE_KEYWORDS:
            break

        if cmd in CONSOLE_COMMANDS:

            if cmd == "/commands":
                console.print()
                for line in COMMANDS_TEXT.splitlines():
                    console.print(f"   {line}")
                console.print()
                continue

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
                    sessions = list_sessions(session_dir)
                    if not sessions:
                        print_error("No sessions to restore.")
                        continue
                    lines = []
                    for i, s in enumerate(sessions, start=1):
                        lines.append(f"{i}. {s['display']}")
                    print_info(["Usage: /restore <number>"] + lines)
                    continue
                try:
                    session_num = int(cmd_parts[1])
                except ValueError:
                    print_error("Usage: /restore <number>. Use /sessions to list them.")
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

            if cmd == "/delete":
                if len(cmd_parts) < 2:
                    sessions = list_sessions(session_dir)
                    if not sessions:
                        print_error("No sessions to delete.")
                        continue
                    lines = []
                    for i, s in enumerate(sessions, start=1):
                        lines.append(f"{i}. {s['display']}")
                    print_info(["Usage: /delete <number>"] + lines)
                    continue
                try:
                    session_num = int(cmd_parts[1])
                except ValueError:
                    print_error("Usage: /delete <number>. Use /sessions to list them.")
                    continue

                sessions = list_sessions(session_dir)
                if session_num < 1 or session_num > len(sessions):
                    print_error(f"Session {session_num} not found. Use /sessions to list them.")
                    continue

                target = sessions[session_num - 1]
                delete_session(target["path"])
                print_success(f"Deleted session from {target['display']}.")
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
                reminder_message = {"role": "user", "content": build_reminder(DESTRUCTIVE_TOOLS)}

                display = StreamDisplay(status="Thinking...")
                stream = chat_stream([system_message] + context + [reminder_message], model, api_key, TOOLS)

                final_message = None

                try:
                    for chunk in stream:
                        if isinstance(chunk, str):
                            display.update(chunk)
                        else:
                            final_message = chunk
                finally:
                    display.finalize()

                if final_message is None:
                    break

                if final_message.get("tool_calls"):
                    context.append(final_message)

                    for call in final_message["tool_calls"]:
                        try:
                            result = run_tool(call, always_allowed)
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
                save_session(session_path, context, model)

                break

        except Exception as e:
            # error print
            print_error(f"Error: {e}")
            continue