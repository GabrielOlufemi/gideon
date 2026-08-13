import hashlib
import json
from pathlib import Path
from datetime import datetime

from config import CONFIG_DIR

SESSIONS_ROOT = CONFIG_DIR / "sessions"


def _timestamp_from_filename(file: Path) -> datetime | None:
    """Parse timestamp from filename like session_2026-07-16_15-42-10.json"""
    timestamp_str = file.stem.removeprefix("session_")
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return None


def _extract_summary(context: list[dict], max_len: int = 80) -> str:
    """Derive a summary from the first user message in the conversation."""
    for msg in context:
        if msg.get("role") == "user" and isinstance(msg.get("content"), str) and msg["content"].strip():
            text = msg["content"].strip()
            if len(text) <= max_len:
                return text
            return text[:max_len].rstrip() + "..."
    return "New session"


def list_sessions(session_dir: Path) -> list[dict]:
    sessions = []

    for file in session_dir.glob("session_*.json"):
        dt = None
        summary = ""
        model = ""

        try:
            with open(file, "r") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        if isinstance(data, dict) and "messages" in data:
            # New format
            summary = data.get("summary", "")
            model = data.get("model", "")
            updated_str = data.get("updated")
            if updated_str:
                try:
                    dt = datetime.strptime(updated_str, "%Y-%m-%d_%H-%M-%S")
                except ValueError:
                    dt = _timestamp_from_filename(file)
            else:
                dt = _timestamp_from_filename(file)
        elif isinstance(data, list):
            # Old format — parse timestamp from filename
            dt = _timestamp_from_filename(file)

        if dt is None:
            continue

        display = dt.strftime("%b %d, %I:%M%p").lstrip("0").replace(" 0", " ")
        if summary:
            display = f"{summary}  \u2014  {display}"

        sessions.append({
            "path": file,
            "display": display,
            "model": model,
            "summary": summary,
        })

    sessions.sort(key=lambda s: s["path"].stem, reverse=True)

    return sessions


def get_session_dir(cwd: str) -> Path:
    cwd_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]
    project_name = Path(cwd).name
    session_dir = SESSIONS_ROOT / f"{cwd_hash}_{project_name}"

    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Could not create session directory {session_dir}: {e}") from e

    return session_dir


def new_session_path(session_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return session_dir / f"session_{timestamp}.json"


def save_session(path: Path, context: list[dict], model: str) -> None:
    """Save session with metadata. Preserves existing created time on re-save."""

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary = _extract_summary(context)

    if path.exists():
        try:
            with open(path, "r") as f:
                existing = json.load(f)
        except (OSError, json.JSONDecodeError):
            existing = {}

        created = existing.get("created", now) if isinstance(existing, dict) else now
    else:
        created = now

    data = {
        "model": model,
        "created": created,
        "updated": now,
        "summary": summary,
        "messages": context,
    }

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        raise RuntimeError(f"Could not write session file {path}: {e}") from e


def load_session(path: Path) -> list[dict]:
    """Return the message list from a session file, handling both old and new formats."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Session file {path} is corrupted: {e}") from e
    except OSError as e:
        raise RuntimeError(f"Could not read session file {path}: {e}") from e

    if isinstance(data, list):
        # Old format — bare message list
        return data

    if isinstance(data, dict) and "messages" in data:
        return data["messages"]

    raise RuntimeError(f"Session file {path} has an unknown format")


def delete_session(path: Path) -> None:
    try:
        path.unlink()
    except OSError as e:
        raise RuntimeError(f"Could not delete session file {path}: {e}") from e