import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".gideon"
CONFIG_PATH= CONFIG_DIR / "config.json"

DEFAULTS = {

    "agent_name" : "Gideon"

}

# reads config file``
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load()

    for key, value in DEFAULTS.items():
        config.setdefault(key,value)

    return config

# saves config file
def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_DIR, "w") as f:
        json.dump(config, f, indent=2)

# retrieves agent name -> incase I decide to change agent name
def get_agent_name() -> str:
    return load_config()["agent_name"]

