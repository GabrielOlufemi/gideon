# src/onboarding.py -> src/gideon/onboarding.py

from gideon.config import save_config, load_config, is_configured
from gideon.display import print_welcome, print_error, print_success, print_tool
from gideon.openrouter import validate_key
from gideon.exceptions import PickerCancelled, AuthError, NoCreditsError, NetworkError

import questionary


def run_onboarding() -> None:
    api_key = collect_api_key()

    config = load_config()
    config["openrouter_api_key"] = api_key
    save_config(config)

    print_success("Setup complete.")


def collect_api_key() -> str:
    print_tool("Your key looks like: sk-or-v1-...")

    while True:
        api_key = questionary.password("Enter your OpenRouter API key: ").ask()

        if api_key is None:
            raise PickerCancelled("Key entry cancelled by user")

        api_key = api_key.strip()
        
        try:
            is_valid = validate_key(api_key)
        except AuthError:
            print_error("That key was rejected. Check it and try again.")
            continue
        except NoCreditsError:
            print_error("That key is valid but has no remaining credits.")
            continue
        except NetworkError as e:
            print_error(f"Couldn't reach OpenRouter: {e}. Try again in a moment.")
            continue

        if is_valid:
            return api_key
        else:
            print_error("That key has no remaining credits. Try a different key.")
            continue