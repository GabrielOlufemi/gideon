from config import load_config, save_config
from display import print_success
from models import pick_model
from onboarding import collect_api_key
from picker import select_choice
from exceptions import PickerCancelled
from display import print_success, print_error, print_info

import questionary


def open_config() -> None:
    """
    Entry point, called from loop.py when the user types exactly
    '/config' at the chat prompt. Presents a menu, dispatches to
    the chosen action, then returns control back to the caller once
    done or cancelled — mirrors how run_onboarding() owns its own
    flow and just returns when finished.
    """

    choices = [
        questionary.Choice(title="Change model", value="model"),
        questionary.Choice(title="Update API key", value="key"),
        questionary.Choice(title="View current config", value="view"),
        questionary.Choice(title="< Back", value="back"),
    ]

    try:
        choice = select_choice("Config", choices)
    except PickerCancelled:
        return
    

    if choice == "model":
        _update_model()
    elif choice == "key":
        _update_key()
    # elif choice == "agent_name":
    #     _change_agent_name
    elif choice == "view":
        _view_config()
    elif choice == "back":
        return


def _update_key() -> None:

    try:
        new_key = collect_api_key()
    except PickerCancelled:
        return

    config = load_config()
    config["openrouter_api_key"] = new_key
    save_config(config)

    print_success("Api Key updated.")


def _update_model() -> None:

    try:
        new_model = pick_model()
    except PickerCancelled:
        return
    
    config = load_config()
    config["model"] = new_model
    save_config(config)

    print_success("Model Changed.")


def _view_config() -> None:
    config = load_config()
    has_key = config.get("openrouter_api_key") is not None

    print_info([
        f"Model: {config.get('model')}",
        f"API key set: {'yes' if has_key else 'no'}",
    ])




