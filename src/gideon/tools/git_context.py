import subprocess
from gideon.tools.pathsafe import BASE_PATH


GIT_CONTEXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_git_context",
        "description": (
            "Get an overview of the current git state: branch, recent commits, "
            "staged/unstaged changes, and untracked files. Call this proactively "
            "at the start of a task or before making changes to understand where "
            "the project is. Runs freely with no approval needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def get_git_context() -> str:
    """Return a snapshot of git state: branch, recent commits, and working tree status."""

    if not (BASE_PATH / ".git").exists():
        return "Not a git repository (or .git not found)."

    parts = []

    # Current branch
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=BASE_PATH,
        )
        if branch.returncode == 0 and branch.stdout.strip():
            parts.append(f"Branch: {branch.stdout.strip()}")
    except Exception:
        pass

    # Recent commits
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-n", "5"],
            capture_output=True, text=True, timeout=10, cwd=BASE_PATH,
        )
        if log.returncode == 0 and log.stdout.strip():
            parts.append("Recent commits:\n" + log.stdout.strip())
    except Exception:
        pass

    # Working tree status (short format — compact)
    try:
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=10, cwd=BASE_PATH,
        )
        if status.returncode == 0 and status.stdout.strip():
            parts.append("Changes:\n" + status.stdout.strip())
        else:
            parts.append("Working tree clean.")
    except Exception:
        pass

    # Diff stat for unstaged changes
    try:
        diff = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=10, cwd=BASE_PATH,
        )
        if diff.returncode == 0 and diff.stdout.strip():
            parts.append("Unstaged diff stat:\n" + diff.stdout.strip())
    except Exception:
        pass

    return "\n\n".join(parts) if parts else "No git information available."
