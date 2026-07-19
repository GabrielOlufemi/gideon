# src/onboarding.py

from config import save_config, is_configured
from display import print_welcome, print_error, print_tool
from models import RECOMMENDED_MODELS, fetch_all_models
from openrouter import validate_key
from picker import select_choice
from exceptions import PickerCancelled, AuthError, NoCreditsError, NetworkError

from pathlib import Path

import questionary


def run_onboarding() -> None:
    """
    Entry point called from main.py 
    """
    # bootup design stuff
    print_welcome(str(Path.cwd()))

    model = pick_model()
    api_key = collect_api_key()

    save_config({
        "model": model,
        "openrouter_api_key": api_key,
    })


def pick_model() -> str:
    choices = []

    # group RECOMMENDED_MODELS by provider, preserving the order providers
    # first appear in — Separator renders as a real line but can't be
    # selected, so it acts as a proper section header, not just a label
    
    seen_providers = []
    grouped = {}
    for m in RECOMMENDED_MODELS:
        if m["provider"] not in grouped:
            grouped[m["provider"]] = []
            seen_providers.append(m["provider"])
        grouped[m["provider"]].append(m)

    for provider in seen_providers:
        choices.append(questionary.Separator(f"\n{provider.upper()}"))
        for m in grouped[provider]:
            choices.append(questionary.Choice(title=f"  {m['label']}", value=m["id"]))

    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="Show all models", value="SHOW ALL"))

    result = select_choice("Choose a model", choices)

    if result != "SHOW ALL":
        return result

    all_models = fetch_all_models()

    fallback_choices = [
        questionary.Choice(title=f"{m['name']}", value=m["id"])
        for m in all_models
    ]

    return select_choice("Choose a model:", fallback_choices)

def collect_api_key() -> str:
    print_tool("Your key looks like: sk-or-v1-...")

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