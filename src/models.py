# src/models.py

from openrouter import fetch_models

# models i think are good 
RECOMMENDED_MODELS = [
    {"id": "anthropic/claude-opus-4.8",  "label": "Claude Opus 4.8",  "provider": "Anthropic"},
    {"id": "anthropic/claude-sonnet-5",  "label": "Claude Sonnet 5",  "provider": "Anthropic"},
    {"id": "anthropic/claude-haiku-4.5", "label": "Claude Haiku 4.5", "provider": "Anthropic"},

    {"id": "openai/gpt-5.6-sol", "label": "GPT-5.6 Sol", "provider": "OpenAI"},
    {"id": "openai/gpt-5.5",     "label": "GPT-5.5",     "provider": "OpenAI"},

    {"id": "google/gemini-3.1-pro",   "label": "Gemini 3.1 Pro",   "provider": "Google"},
    {"id": "google/gemini-3.5-flash", "label": "Gemini 3.5 Flash", "provider": "Google"},

    {"id": "deepseek/deepseek-v4-pro",       "label": "DeepSeek V4 Pro",        "provider": "DeepSeek"},
    {"id": "deepseek/deepseek-v4-flash",     "label": "DeepSeek V4 Flash",      "provider": "DeepSeek"},
    {"id": "deepseek/deepseek-v3.2-speciale","label": "DeepSeek V3.2 Speciale", "provider": "DeepSeek"},
]


def fetch_all_models() -> list[dict]:
    raw_models = fetch_models()

    usable = [
        m for m in raw_models
        if "text" in m.get("architecture", {}).get("input_modalities", [])
        and "text" in m.get("architecture", {}).get("output_modalities", [])
    ]

    return usable