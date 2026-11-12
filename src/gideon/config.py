import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".gideon"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    "agent_name": "Gideon",
    "model": None,
    "openrouter_api_key": None,
    "context_length": None,
    "total_tokens_used": 0,
}

_config_cache: dict | None = None


def load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not CONFIG_PATH.exists():
        _config_cache = dict(DEFAULTS)
        return _config_cache

    with open(CONFIG_PATH, "r") as f:
        _config_cache = json.load(f)

    for key, value in DEFAULTS.items():
        _config_cache.setdefault(key, value)

    return _config_cache


def save_config(config: dict) -> None:
    global _config_cache
    _config_cache = config
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

# retrieves agent name -> incase I decide to change agent name
def get_agent_name() -> str:
    return load_config()["agent_name"]

# exists on startup to know if setup has occurred before
def is_configured() -> bool:
    config = load_config()
    return config.get("openrouter_api_key") is not None

def get_context_length() -> int | None:
    return load_config().get("context_length")

def set_context_length(value: int) -> None:
    config = load_config()
    config["context_length"] = value
    save_config(config)

def get_total_tokens_used() -> int:
    return load_config().get("total_tokens_used", 0)

def set_total_tokens_used(value: int) -> None:
    config = load_config()
    config["total_tokens_used"] = value
    save_config(config)