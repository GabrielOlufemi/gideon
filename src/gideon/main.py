from pathlib import Path

from gideon.session_manager import get_session_dir, load_session
from gideon.picker import pick_session
from gideon.exceptions import PickerCancelled

from gideon.loop import run_loop

from gideon.system_prompt import build_system_prompt

from gideon.config import get_agent_name, is_configured, load_config, save_config

from gideon.onboarding import run_onboarding
from gideon.models import pick_model

from gideon.display import print_welcome

from gideon.tools_config import TOOLS, DESTRUCTIVE_TOOLS
from gideon.display import VERSION

import sys

def main() -> None:

    if "--version" in sys.argv:
        print(f"gideon v{VERSION}")
        return

    print_welcome(str(Path.cwd()))

    if not is_configured():
        try:
            run_onboarding()
        except PickerCancelled:
            print("Setup cancelled. Exiting")
            return

    try:
        model = pick_model()
    except PickerCancelled:
        print("No model selected. Exiting")
        return

    config = load_config()
    config["model"] = model
    save_config(config)

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
        # system_prompt = build_system_prompt(get_agent_name(), TOOLS, DESTRUCTIVE_TOOLS)
        # context.append({"role": "system", "content": system_prompt})

    run_loop(context, session_path, session_dir)
    
if __name__ == "__main__":
    main()