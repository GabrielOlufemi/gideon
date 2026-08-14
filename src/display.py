import difflib
import re
import sys

from rich.console import Console
from rich.panel import Panel
from rich.box import Box
from rich.padding import Padding
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from rich import box


VERSION = "0.1.0"


COLORS = {
    "user_input": "on grey19",
    "accent": "#239054",
    "tool_detail": "dim",
    "reply": "default",
    "error": "#FF4444",
}

INDENT = (0, 0, 0, 3)  # top, right, bottom, left — single source of truth for spacing

LEFT_ONLY = Box(
    "    \n"
    "│   \n"
    "│   \n"
    "│   \n"
    "│   \n"
    "│   \n"
    "│   \n"
    "    \n"
)

console = Console()
CODE_INDENT = (0, 0, 0, 5)

def print_user(message: str) -> None:
    """Print user input, handling multiline messages properly."""
    lines = message.splitlines()
    for line in lines:
        console.print(f"> {line}".ljust(console.width), style=COLORS["user_input"])
    console.print()
    console.print(Rule(style="dim"))
    console.print("   Ctrl+C to interrupt", style=COLORS["tool_detail"])
    

def print_top_rule() -> None:
    console.print(Rule(style="dim"))

def print_context_bar(prompt_tokens: int, completion_tokens: int, context_length: int | None) -> None:
    """Print a compact context usage indicator, Claude-style."""
    if not context_length or context_length <= 0:
        return

    total = prompt_tokens + completion_tokens
    pct = min(100, int((total / context_length) * 100))

    bar_len = 20
    filled = int((pct / 100) * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    if pct >= 90:
        style = "bold red"
    elif pct >= 75:
        style = "bold yellow"
    else:
        style = "dim"

    console.print(Padding(
        f"[{style}]{bar}  [{pct}%]  {total:,}/{context_length:,} tokens[/{style}]",
        (0, 0, 0, 3),
    ))


def print_tool(message: str) -> None:
    console.print(f"   {message}", style=COLORS["tool_detail"])


def print_tool_summary(name: str, detail: str) -> None:
    """Print a compact single-line tool summary, Claude Code style."""
    console.print(f"   [{COLORS['accent']}]{name}:[/{COLORS['accent']}] {detail}")


class StreamDisplay:
    """Wraps Rich's Live display to render streaming content with Markdown.

    Shows an optional status message (e.g. "Thinking...") before content arrives.
    The status is replaced seamlessly when the first content token comes in.
    """

    def __init__(self, status: str | None = None):
        self._content = ""
        self._live = None
        self._status = status
        self._has_content = False

        if status:
            # Show the status panel immediately
            self._show_status()

    def _show_status(self) -> None:
        """Render the status message as a dim panel."""
        panel = Padding(
            Panel(
                Text(self._status, style="dim"),
                box=LEFT_ONLY,
                border_style=COLORS["accent"],
                padding=(0, 1),
            ),
            INDENT,
        )
        self._live = Live(panel, refresh_per_second=15, transient=False)
        self._live.start()

    def _show_content(self) -> None:
        """Switch from status to content renderable."""
        panel = Padding(
            Panel(
                Markdown(self._content, code_theme="monokai"),
                box=LEFT_ONLY,
                border_style=COLORS["accent"],
                padding=(0, 1),
            ),
            INDENT,
        )
        if self._live is None:
            self._live = Live(panel, refresh_per_second=15, transient=False)
            self._live.start()
        else:
            self._live.update(panel)

    def update(self, token: str) -> None:
        """Append a token and refresh the rendered display."""
        self._content += token
        if not self._content.strip():
            return

        if not self._has_content:
            self._has_content = True
            self._show_content()
        else:
            panel = Padding(
                Panel(
                    Markdown(self._content, code_theme="monokai"),
                    box=LEFT_ONLY,
                    border_style=COLORS["accent"],
                    padding=(0, 1),
                ),
                INDENT,
            )
            self._live.update(panel)

    def finalize(self) -> None:
        """Stop the live display, leaving the final renderable on screen."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    @property
    def content(self) -> str:
        return self._content


def print_reply(message: str) -> None:
    parts = re.split(r"(```[\s\S]*?```)", message)

    for part in parts:
        if not part.strip():
            continue

        if part.startswith("```"):
            console.print(Padding(Markdown(part, code_theme="monokai"), CODE_INDENT))
        else:
            console.print(Padding(
                Panel(
                    Markdown(part.strip(), code_theme="monokai"),
                    box=LEFT_ONLY,
                    border_style=COLORS["accent"],
                    expand=False,
                    padding=(0, 1),
                ),
                INDENT,
            ))


def print_error(message: str) -> None:
    console.print(f"   {message}", style=COLORS["error"])


def print_permission(name: str, details: str) -> None:
    console.print()
    console.print(Padding(
        Panel(
            details,
            title=f"{name}",
            title_align="left",
            border_style=COLORS["accent"],
            box=box.SQUARE,
            expand=False,
            padding=(0, 1),
        ),
        INDENT,
    ))
    console.print()


def print_edit_diff(path: str, old_content: str | None, old_string: str, new_string: str) -> None:
    """Unified diff for edit_file, Claude Code style."""
    if old_content is None:
        return

    # Replace old_string with new_string in the full content
    modified = old_content.replace(old_string, new_string, 1)
    if modified == old_content:
        return  # nothing changed, bail

    old_lines = old_content.splitlines(keepends=True)
    new_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{path}", tofile=f"b/{path}",
        n=3,
    )

    diff_text = "".join(diff)
    if not diff_text.strip():
        return

    console.print()
    console.print(
        Padding(
            Syntax(diff_text, "diff", line_numbers=False),
            INDENT,
        )
    )


def print_write_summary(path: str, old_exists: bool, line_count: int) -> None:
    """Minimal summary for write_file. No content dump, just path and size."""
    label = "Overwrite" if old_exists else "New file"
    console.print()
    console.print(Padding(
        Panel(
            f"{label} — {line_count} lines",
            title=f"  {path}",
            title_align="left",
            border_style=COLORS["accent"],
            box=box.SQUARE,
            padding=(0, 1),
            expand=False,
        ),
        INDENT,
    ))
    console.print()


# welcome stuff

def print_welcome(cwd: str) -> None:
    left = (
        f"[bold]Current Path:[/bold] [dim]{cwd}[/dim]\n"
        # "No model selected yet"
        "\n\n[bold]/commands[/bold] [dim]to view all commands"
        "\n[bold]/exit[/bold] [dim]to leave interface"

    )

    right = (
        "[bold]Setup[/bold]\n"
        "1. Choose a model\n"
        "2. Add your OpenRouter key\n\n"
        "[bold]Who is Gideon?[/bold] \nhey, i'm gideon, gabriel's alter ego (sort of) and "
        "your terminal coding agent. Point me at a problem and I'll "
        "poke through your codebase, run commands and do the heavy lifting while you sit back and relax."
        " I'll simply check with you first before doing anything permanent."
    )

    layout = Table(box=box.SQUARE, show_header=False, show_edge=False, padding=(0, 2), expand=True)
    layout.add_column(ratio=1)
    layout.add_column(ratio=2)
    layout.add_row(left, right)

    console.print()
    console.print(
        Panel(
            layout,
            title=f"Gideon v{VERSION}",
            title_align="left",
            border_style=COLORS["accent"],
            box=box.SQUARE,
            expand=True,
            padding=(0, 2),
        )
    )
    console.print()

def print_success(message: str) -> None:
    console.print()
    console.print(f"   [{COLORS['accent']}]{message}[/{COLORS['accent']}]")
    console.print()

def print_info(lines: list[str]) -> None:
    console.print()
    for line in lines:
        console.print(f"   [{COLORS['accent']}]{line}[/{COLORS['accent']}]")
    console.print()