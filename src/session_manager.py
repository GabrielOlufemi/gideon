import hashlib
import json
from pathlib import Path
from datetime import datetime

SESSIONS_ROOT = Path.home() / ".eureka" / "sessions"
# e.g. does something like: home/gabriel/.eureka/sessions

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


def get_session_dir(cwd: str) -> Path:

    # - hash cwd with sha256, truncate to 12 hex chars
    # - pull the last path component off cwd for the human-readable suffix
    # - join SESSIONS_ROOT / f"{hash}_{name}"
    # - mkdir(parents=True, exist_ok=True)

    cwd_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]

    project_name = Path(cwd).stem

    session_dir = SESSIONS_ROOT / f"{cwd_hash}_{project_name}"

    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Could not create session directory {session_dir}: {e}") from e

    return session_dir

