# imports
from pathlib import Path
import questionary

from exceptions import PickerCancelled

from session_manager import list_sessions, new_session_path



# session picker
def pick_session(session_dir: Path) -> Path:
    sessions = list_sessions(session_dir)

    if not sessions:
        return new_session_path(session_dir)
    
    choices = [
        questionary.Choice(
            title="New session",
            value=new_session_path(session_dir)
        )
    ]

    choices += [
        questionary.Choice(
            title=session["display"],
            value=session["path"]
        )

        for session in sessions
    ]

    # result is already a Path at this point, whichever option got picked
    result = select_choice("Select a session:", choices)

    return result
    

def select_choice(message: str, choices: list[questionary.Choice]):

    result = questionary.select(message, choices=choices.ask())

    if result is None:
        raise PickerCancelled("Selection cancelled by user")

    return result