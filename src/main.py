from pathlib import Path

from session_manager import get_session_dir, load_session
from picker import pick_session
from exceptions import PickerCancelled

from loop import run_loop


def main() -> None:
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

    run_loop(context, session_path)
    
if __name__ == "__main__":
    main()