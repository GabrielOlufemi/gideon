from pathlib import Path

from session_manager import get_session_dir, load_session
from picker import pick_session
from exceptions import PickerCancelled

from loop import run_loop

# prompt import
from system_prompt import build_system_prompt

# config.py import
from config import get_agent_name, is_configured

# tool related imports
from tools_config import TOOLS, DESTRUCTIVE_TOOLS

# onboarding import
from onboarding import run_onboarding

def main() -> None:

    if not is_configured():
        try:
            run_onboarding()
        except PickerCancelled:
            print("Setup cancelled. Exiting")
            return

    cwd = Path.cwd()

    session_dir = get_session_dir(str(cwd))

    try:
        session_path = pick_session(session_dir)
    except PickerCancelled:
        print("No session selected. Exiting")
        return
    
    if session_path.exists():
        context = load_session(session_path)
    else:
        context = []
        # retrieving system prompt
        system_prompt = build_system_prompt(get_agent_name(), TOOLS, DESTRUCTIVE_TOOLS)
        context.append({"role": "system", "content": system_prompt})


    # loop exec
    run_loop(context, session_path)
    
if __name__ == "__main__":
    main()