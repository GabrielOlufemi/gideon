import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".gideon"
CONFIG_PATH= CONFIG_DIR / "config.json"

DEFAULTS = {
    "agent_name" : "Gideon",
    "model" : None,
    "openrouter_api_key" : None,
    "context_length": None,
    "total_tokens_used": 0,
    "system_prompt_tokens": 0,
}

# reads config file``
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    for key, value in DEFAULTS.items():
        config.setdefault(key,value)

    return config

# saves config file
def save_config(config: dict) -> None:
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

def get_system_prompt_tokens() -> int:
    return load_config().get("system_prompt_tokens", 0)

def set_system_prompt_tokens(value: int) -> None:
    config = load_config()
    config["system_prompt_tokens"] = value
    save_config(config)