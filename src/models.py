# src/models.py

import questionary

from openrouter import fetch_models
from picker import select_choice
from config import set_context_length

RECOMMENDED_MODELS = [
    {"id": "anthropic/claude-opus-4.8",  "label": "Claude Opus 4.8",  "provider": "Anthropic"},
    {"id": "anthropic/claude-sonnet-5",  "label": "Claude Sonnet 5",  "provider": "Anthropic"},
    {"id": "anthropic/claude-haiku-4.5", "label": "Claude Haiku 4.5", "provider": "Anthropic"},

    {"id": "deepseek/deepseek-v4-pro",       "label": "DeepSeek V4 Pro",        "provider": "DeepSeek"},
    {"id": "deepseek/deepseek-v4-flash",     "label": "DeepSeek V4 Flash",      "provider": "DeepSeek"},
    {"id": "deepseek/deepseek-v3.2-speciale","label": "DeepSeek V3.2 Speciale", "provider": "DeepSeek"},

    {"id": "google/gemini-3.1-pro",   "label": "Gemini 3.1 Pro",   "provider": "Google"},
    {"id": "google/gemini-3.5-flash", "label": "Gemini 3.5 Flash", "provider": "Google"},

    {"id": "openai/gpt-5.6-sol", "label": "GPT-5.6 Sol", "provider": "OpenAI"},
    {"id": "openai/gpt-5.5",     "label": "GPT-5.5",     "provider": "OpenAI"},
]


def fetch_all_models() -> list[dict]:
    raw_models = fetch_models()
    recommended_ids = {m["id"] for m in RECOMMENDED_MODELS}

    usable = [
        m for m in raw_models
        if "text" in m.get("architecture", {}).get("input_modalities", [])
        and "text" in m.get("architecture", {}).get("output_modalities", [])
        and m.get("id") not in recommended_ids
    ]

    return usable


def _lookup_context_length(model_id: str, all_models: list[dict] | None = None) -> int | None:
    """Look up context_length for a given model ID from the OpenRouter model list."""
    if all_models is None:
        try:
            all_models = fetch_models()
        except Exception:
            return None

    for m in all_models:
        if m.get("id") == model_id:
            return m.get("context_length")

    return None


def pick_model() -> str:
    choices = []
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

    # Fetch the raw model list once upfront; use for both recommended and full paths
    raw_models = fetch_models()

    if result != "SHOW ALL":
        ctx_len = _lookup_context_length(result, raw_models)
        if ctx_len:
            set_context_length(ctx_len)
        return result

    recommended_ids = {m["id"] for m in RECOMMENDED_MODELS}
    usable = [
        m for m in raw_models
        if "text" in m.get("architecture", {}).get("input_modalities", [])
        and "text" in m.get("architecture", {}).get("output_modalities", [])
        and m.get("id") not in recommended_ids
    ]

    fallback_choices = [
        questionary.Choice(title=f"{m['name']}", value=m["id"])
        for m in usable
    ]

    picked = select_choice("Choose a model:", fallback_choices)

    ctx_len = _lookup_context_length(picked, raw_models)
    if ctx_len:
        set_context_length(ctx_len)

    return picked