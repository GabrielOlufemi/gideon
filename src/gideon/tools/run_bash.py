import subprocess
import time
import threading
from queue import Queue, Empty

from rich.panel import Panel
from rich.padding import Padding
from rich.live import Live
from rich.text import Text

from gideon.tools.pathsafe import BASE_PATH
from gideon.display import COLORS, LEFT_ONLY, INDENT

BASH_TIMEOUT_SECONDS = 120
LIVE_MAX_LINES = 30


RUN_BASH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_bash",
        "description": (
            "Run a shell command in the project's root directory and return its "
            "exit code, stdout, and stderr. Use this for things read_file, "
            "write_file, and list_directories can't do — running tests, installing "
            "packages, checking git status, running scripts, and similar tasks. "
            "This command always requires the user's explicit approval before it "
            "runs, so prefer the more targeted file tools when they're sufficient."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "A single shell command line to execute, exactly as you'd "
                        "type it in a terminal (e.g. 'pytest', 'git status', "
                        "'pip install requests'). Multiple commands can be chained "
                        "with '&&' or ';'."
                    )
                },
                "description": {
                    "type": "string",
                    "description": (
                        "A very brief 1-2 sentence explanation of what this "
                        "command does and why it's being run. Helps the user "
                        "understand what they're approving."
                    )
                }
            },
            "required": ["command", "description"]
        }
    }
}


def _reader(pipe, queue: Queue) -> None:
    """Read lines from a pipe into a queue."""
    try:
        for line in iter(pipe.readline, ""):
            queue.put(line)
    finally:
        pipe.close()


def _drain(queue: Queue) -> list[str]:
    """Non-blocking drain of all available items from a queue."""
    lines = []
    while True:
        try:
            lines.append(queue.get_nowait())
        except Empty:
            break
    return lines


def run_bash(command: str) -> str:

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=BASE_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except Exception as e:
        return f"Error running '{command}': {e}"

    out_queue: Queue = Queue()
    err_queue: Queue = Queue()

    out_thread = threading.Thread(target=_reader, args=(process.stdout, out_queue))
    err_thread = threading.Thread(target=_reader, args=(process.stderr, err_queue))
    out_thread.daemon = True
    err_thread.daemon = True
    out_thread.start()
    err_thread.start()

    start = time.time()
    out_lines: list[str] = []
    err_lines: list[str] = []
    timed_out = False

    # Build the live display panel
    text = Text("", style="default")
    panel = Padding(
        Panel(text, box=LEFT_ONLY, border_style=COLORS["accent"], padding=(0, 1)),
        INDENT,
    )

    with Live(panel, refresh_per_second=15, transient=True) as live:

        while process.poll() is None:
            elapsed = time.time() - start
            if elapsed > BASH_TIMEOUT_SECONDS:
                process.kill()
                timed_out = True
                break

            new_out = _drain(out_queue)
            new_err = _drain(err_queue)

            if new_out or new_err:
                out_lines.extend(new_out)
                err_lines.extend(new_err)
                _render_panel(live, panel, text, out_lines, err_lines)

            time.sleep(0.05)

        out_thread.join(timeout=2)
        err_thread.join(timeout=2)

        # Final drain
        new_out = _drain(out_queue)
        new_err = _drain(err_queue)
        if new_out or new_err:
            out_lines.extend(new_out)
            err_lines.extend(new_err)

        # Show final output before closing
        if out_lines or err_lines:
            _render_panel(live, panel, text, out_lines, err_lines)

    if timed_out:
        return (
            f"Error: command timed out after {BASH_TIMEOUT_SECONDS} seconds\n"
            f"stdout: {''.join(out_lines)}\n"
            f"stderr: {''.join(err_lines)}"
        )

    return (
        f"exit code: {process.returncode}\n"
        f"stdout: {''.join(out_lines)}\n"
        f"stderr: {''.join(err_lines)}"
    )


def _render_panel(
    live: Live,
    panel: Padding,
    text: Text,
    out_lines: list[str],
    err_lines: list[str],
) -> None:
    """Show the tail of stdout+stderr in the live panel."""
    all_show = out_lines + err_lines
    if len(all_show) > LIVE_MAX_LINES:
        all_show = all_show[-LIVE_MAX_LINES:]
    text.text = "".join(all_show)
    live.update(panel)
