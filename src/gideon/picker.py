# imports
from pathlib import Path
import questionary


from gideon.exceptions import PickerCancelled
from typing import Any
from gideon.session_manager import list_sessions, new_session_path

# styling p
custom_style = questionary.Style([
    ('qmark', 'fg:#239054 bold'),
    ('pointer', 'fg:#239054 bold'),
    ('highlighted', 'fg:#239054 bold'),
    ('answer', 'fg:#239054 bold'),
])

# session picker
def pick_session(session_dir: Path) -> Path:
    sessions = list_sessions(session_dir)

    if not sessions:
        return new_session_path(session_dir)
    
    choices = [
        questionary.Choice(
            title="1. New session",
            value=new_session_path(session_dir)
        )
    ]

    choices += [
        questionary.Choice(
            title=f"{i}. {session["display"]}",
            value=session["path"]
        )

        for i, session in enumerate(sessions, start=2)
    ]

    # result is already a Path at this point, whichever option got picked
    # looks someething like this 
    # PosixPath('/home/gabriel/.gideon/sessions/bd58ed479e5c_test_project/session_2026-07-16_15-42-10.json')
    result = select_choice("Select a session:", choices)

    return result
    

def select_choice(message: str, choices: list[questionary.Choice]) -> Any:

    result = questionary.select(
        message, 
        choices=choices,
        style=custom_style,
        pointer="\u276f",
        qmark=""
    ).ask()

    if result is None:
        raise PickerCancelled("Selection cancelled by user")

    return result