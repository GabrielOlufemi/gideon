import json
from openrouter import chat

# scaffolding stuff
from pathlib import Path
from session_manager import save_session

# color config imports 
from display import (
    print_error, print_reply, print_tool, print_permission,print_user
)

# tool + model related stuff
from tools.read_file import read_file
from tools.write_file import write_file
from tools.list_directories import list_directories
from tools.run_bash import run_bash

from tools_config import MODEL, TOOLS, DESTRUCTIVE_TOOLS

ALWAYS_ALLOWED = []

# terminate words
TERMINATE_KEYWORDS = ["quit", "exit", "leave"]

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

    return f"Error: unknown tool '{name}'"


# permission request logic
def request_permission(name: str, arguments: dict[str, str]) -> str:

    if name == "write_file":
        details = f"path: {arguments.get('path')}"
    elif name == "run_bash":
        details = f"command: {arguments.get('command')}"
    else:
        details = f"arguments: {arguments}"

    allow_always = name != "run_bash"

    if allow_always:
        options = "[1] allow once\n[2] always allow\n[3] deny"
    else:
        options = "[1] allow once\n[2] deny"

    print_permission(name, details, options)

    choice = input("> ").strip()

    if choice == "1":
        return "yes"
    elif allow_always and choice == "2":
        return "always"
    elif (allow_always and choice == "3") or (not allow_always and choice == "2"):
        return "no"
    else:
        # error print
        print_error("Invalid choice, denying by default.")
        return "no"


def run_loop(context: list[dict], session_path: Path) -> None:
    while True:

        user_input = input("> ")
        print_user(user_input)

        # check if input attempts termiante
        if user_input.strip().lower() in TERMINATE_KEYWORDS:
            break

        # check if input is empty
        if user_input.strip().lower() == "":
            # error print
            print_error("Type in something big dawg")
            continue

        # start of a turn
        # add to context
        context.append({
            "role":"user", "content":user_input
        })

        try:
            
            while True:
                response = chat(context, MODEL, TOOLS)
                message = response["choices"][0]["message"]

                if message.get("tool_calls"):
                    context.append(message)

                    # set of ids model promises to call for this turn
                    tool_call_ids = {call["id"] for call in message["tool_calls"]}

                    # set of ids actually called + successfully executed
                    answered_ids = set()

                    try:
                        for call in message["tool_calls"]:
                            
                            result = run_tool(call)

                            # tool call completion
                            print_tool(f"Done.")

                            context.append({
                                "role" : "tool",
                                "tool_call_id" : call["id"],
                                "content" : result
                            })

                            answered_ids.add(call["id"])
                    except Exception as e:
                    
                        #missing tool calls that never got a corresponding tool response
                        missing_ids = tool_call_ids - answered_ids

                        for missing_id in missing_ids:
                            context.append({
                                "role" : "tool",
                                "tool_call_id" : missing_id,
                                "content" : f"Error: {e}"
                            })


                    continue

                reply_text = message["content"]

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
        
        # default response print
        print_reply(f"\n{reply_text}")