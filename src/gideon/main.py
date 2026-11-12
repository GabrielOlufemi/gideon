from pathlib import Path

from gideon.session_manager import get_session_dir, load_session, get_session_metadata
from gideon.picker import pick_session
from gideon.exceptions import PickerCancelled

from gideon.loop import run_loop

from gideon.config import is_configured, load_config, save_config

from gideon.onboarding import run_onboarding
from gideon.models import pick_model

from gideon.display import print_welcome, print_history
from gideon.display import VERSION

import questionary
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

    config = load_config()
    saved_model = config.get("model")
    if saved_model:
        model = saved_model
    else:
        try:
            model = pick_model()
        except PickerCancelled:
            print("No model selected. Exiting")
            return
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
        metadata = get_session_metadata(session_path)
        auto_mode = metadata.get("auto_mode", False)
        if context:
            print_history(context)
    else:
        context = []
        auto_mode = questionary.confirm("Enable auto mode?", default=False).ask()
        if auto_mode is None:
            auto_mode = False

    run_loop(context, session_path, session_dir, auto_mode)
    
if __name__ == "__main__":
    main()