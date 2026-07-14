import hashlib
import json
from pathlib import Path
from datetime import datetime

SESSIONS_ROOT = Path.home() / ".eureka" / "sessions"

def list_sessions(session_dir: Path) -> list[dict]: 

    sessions = []

    for file in session_dir.glob("session_*.json"):
        # filename looks like: session_2026-07-12_14-30-05.json
        timestamp_str = file.stem.removeprefix("session_")

        try:
            dt = datetime.strptime(timestamp_str, f"%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue

        sessions.append({
            "path" : file,
            "display": dt.strftime("%b %d, %I:%M%p").lstrip("0").replace(" 0", " ")
        })

    sessions.sort(key=lambda s: s["path"].stem, reverse=True)

    return sessions