import json
from openrouter import chat


# tool imports
from tools.read_file import read_file, READ_FILE_SCHEMA
from tools.list_directories import list_directories, LIST_DIRECTORIES_SCHEMA
from tools.write_file import write_file, WRITE_FILE_SCHEMA
from tools.run_bash import run_bash, RUN_BASH_SCHEMA

MODEL = "google/gemini-2.5-flash"
TOOLS = [
    READ_FILE_SCHEMA, 
    WRITE_FILE_SCHEMA, 
    LIST_DIRECTORIES_SCHEMA,
    RUN_BASH_SCHEMA
]

DESTRUCTIVE_TOOLS = ["write_file", "run_bash"]
ALWAYS_ALLOWED = []

# stores conversation history per session
context = []


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
        print(f"Reading {arguments["path"]}...")
        return read_file(arguments["path"])


    if name == "write_file":
        print(f"Writing to {arguments["path"]}...")
        return write_file(arguments["path"], arguments["content"])


    if name == "list_directories":
        print(f"Listing {arguments["dir_path"]}...")
        return list_directories(arguments["dir_path"])
    

    return f"Error: unknown tool '{name}'"


def request_permission(name: str, arguments: dict[str, str]) -> str:
    print(f"\n Eureka wants to run the following '{name}' with the following: ")

    if name == "write_file":
        print(f"  path: {arguments.get("path")}")
        # print(f"  content: {arguments.get("content")}")
    elif name=="run_bash":
        print(f"  command: {arguments.get("command")}")
    else:
        print(f"  arguments: {arguments}")


    allow_always = name != "run_bash"

    print(f"\n [1] allow once")

    if allow_always:
        print(f"\n [2] always allow")
        print(f"\n [3] deny")
    else:
        print(f"\n [2] deny")

    choice = input("> ").strip()

    if choice == "1":
        return "yes"
    elif allow_always and choice == "2":
        return "always"
    elif (allow_always and choice == "3") or (not allow_always and choice == "2"):
        return "no"
    else:
        print("Invalid choice, denying by default.")
        return "no"


while True:

    user_input = input("> ")

    # check if input is exit
    if user_input.strip().lower() == "exit":
        break

    # check if input is empty
    if user_input.strip().lower() == "":
        print ("Type in something big dawg")
        continue

    context.append({
        "role":"user", "content":user_input
    })
    
    try:
        
        while True:
            response = chat(context, MODEL, TOOLS)
            message = response["choices"][0]["message"]

            if message.get("tool_calls"):
                context.append(message)

                for call in message["tool_calls"]:

                    result = run_tool(call)
                    print(f"Done.")

                    context.append({
                        "role" : "tool",
                        "tool_call_id" : call["id"],
                        "content" : result
                    })

                continue

            reply_text = message["content"]

            context.append({
                "role":"assistant", "content":reply_text
            })

            break
   
   
    except Exception as e:
        print(f"Error: {e}")
        if (context[-1]["role"]) != "tool":
            context.pop()
        continue

    print(f"\n{reply_text}")