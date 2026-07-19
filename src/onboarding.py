# src/onboarding.py

from config import save_config, is_configured
from display import print_welcome, print_error
from models import RECOMMENDED_MODELS, fetch_all_models
from openrouter import validate_key
from picker import select_choice
from exceptions import PickerCancelled, AuthError, NoCreditsError, NetworkError

import questionary


def run_onboarding() -> None:
    """
    Entry point called from main.py 
    """
    # bootup design stuff
    print_welcome()

    model = pick_model()
    api_key = collect_api_key()

    save_config({
        "model": model,
        "openrouter_api_key": api_key,
    })


def pick_model() -> str:
    """
    TODO: build the questionary.select list.
    Open question we haven't settled: does 'Show all models' sit as
    the last item in the same flat list as RECOMMENDED_MODELS, or is
    it a separate second prompt? Flat list matches picker.py's existing
    'New session' pattern, so that's the current lean, not yet decided.
    """

    choices = [
        questionary.Choice(
            title=f"{m['label']} ({m['provider']})",
            value=m["id"]
        )

        for m in RECOMMENDED_MODELS
    ]

    choices.append(
        questionary.Choice(title="Show all models", value="SHOW ALL")
    )

    result = select_choice("Choose a model", choices)

    if result != "SHOW ALL":
        return result
    
    # escape hatch: fetch_all_models() hits OpenRouter live and is responsible
    # for filtering out non-text models before it ever returns here — this
    # function shouldn't need to know what "usable" means, just consume it
    all_models = fetch_all_models()

    fallback_choices = [
        questionary.Choice(
            title=f"{m['name']}",
            value=m["id"]
        )
        for m in all_models
    ]

    # second prompt, same pattern, no further branching needed after this —
    # there's no third tier of "show even more"
    return select_choice("Choose a model:", fallback_choices)


def collect_api_key() -> str:

    while True:
        api_key = questionary.password("Enter your OpenRouter API key: ").ask()

        if api_key is None:
            raise PickerCancelled("Key entry cancelled by user")
        
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