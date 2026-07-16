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


    # sessions looks something like this :
    # [
    #     {
    #         "path": PosixPath("/home/gabriel/.eureka/sessions/a3f9c21e8b4d_test_project/session_2026-07-14_09-15-42.json"),
    #         "display": "Jul 14, 9:15AM"
    #     },
    #     {
    #         "path": PosixPath("/home/gabriel/.eureka/sessions/a3f9c21e8b4d_test_project/session_2026-07-12_14-30-05.json"),
    #         "display": "Jul 12, 2:30PM"
    #     }
    # ]

    
    return sessions



def get_session_dir(cwd: str) -> Path:

    # - hash cwd with sha256, truncate to 12 hex chars
    # - pull the last path component off cwd for the human-readable suffix
    # - join SESSIONS_ROOT / f"{hash}_{name}"
    # - mkdir(parents=True, exist_ok=True)

    cwd_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]

    project_name = Path(cwd).name

    session_dir = SESSIONS_ROOT / f"{cwd_hash}_{project_name}"
    # looks something like this /home/gabriel/.eureka/sessions/a3f9c21e8b4d_test_project

    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Could not create session directory {session_dir}: {e}") from e

    return session_dir



def new_session_path(session_dir: Path) -> Path:

    timestamp = datetime.now().strftime(f"%Y-%m-%d_%H-%M-%S")

    return session_dir / f"session_{timestamp}.json"



def save_session(path: Path, context: list[dict]) -> None:

    try:
        with open(path, "w") as f:
            json.dump(context, f)

    except OSError as e:
        raise RuntimeError(f"Could not write session file {path}: {e}") from e



def load_session(path: Path) -> list[dict]:

    # - open path, json.load, return it
    # - what happens if the file is corrupted / not valid JSON?
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Session file {path} is corrupted: {e}") from e
    except OSError as e:
        raise RuntimeError(f"Could not read session file {path}: {e}") from e
    
    if not isinstance(data, list):
        # checks if data arrives/matches list
        raise RuntimeError(f"Session file {path} does not contain a valid session list")

    return data