import difflib
import json
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


VERSION = "0.2.0"


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

def print_context_bar(prompt_tokens: int, completion_tokens: int, context_length: int | None, auto_mode: bool = False) -> None:
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

    bar_text = f"[{style}]{bar}  [{pct}%]  {total:,}/{context_length:,} tokens[/{style}]"

    if auto_mode:
        mode_text = Text()
        mode_text.append("mode \u00b7 ", style="bold")
        mode_text.append("/auto", style="bold")
    else:
        mode_text = Text()
        mode_text.append("mode \u00b7 ", style="bold")
        mode_text.append("/manual", style="bold")

    # Right-align mode tag within terminal width
    full = Text.from_markup(bar_text)
    # Calculate padding needed to push mode_text to the right edge
    left_width = len(full.plain)
    mode_width = len(mode_text.plain)
    spacing = max(2, console.width - left_width - mode_width - 4)
    full.append(" " * spacing)
    full.append(mode_text)
    console.print(Padding(full, (0, 0, 0, 3)))


def print_tool(message: str) -> None:
    console.print(f"   {message}", style=COLORS["tool_detail"])


def print_tool_summary(name: str, detail: str) -> None:
    """Print a compact single-line tool summary, Claude Code style."""
    console.print(f"   [{COLORS['accent']}]{name}:[/{COLORS['accent']}] {detail}")


class StreamDisplay:
    """Wraps Rich's Live display to render streaming content with Markdown.

    Shows an optional status message (e.g. "Thinking...") before content arrives.
    The status is replaced seamlessly when the first content token comes in.

    Horizontal rule patterns (---, ***, ___) are stripped from the displayed
    content because they're ugly in a streaming terminal UI and the model adds
    them despite being told not to.
    """

    def __init__(self, status: str | None = None):
        self._content = ""
        self._live = None
        self._status = status
        self._has_content = False

        if status:
            # Show the status panel immediately
            self._show_status()

    def _strip_horizontal_rules(self, text: str) -> str:
        """Remove Markdown horizontal rule lines from display content."""
        text = re.sub(r'^[ \t]*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*(-\s+){2,}-?\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

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

    def _render_panel(self) -> Padding:
        """Build the current panel from content, stripping HRs."""
        cleaned = self._strip_horizontal_rules(self._content)
        return Padding(
            Panel(
                Markdown(cleaned, code_theme="monokai"),
                box=LEFT_ONLY,
                border_style=COLORS["accent"],
                padding=(0, 1),
            ),
            INDENT,
        )

    def _show_content(self) -> None:
        """Switch from status to content renderable."""
        panel = self._render_panel()
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
            self._live.update(self._render_panel())

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
            f"{label} \u2014 {line_count} lines",
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
        "\n\n[bold]/commands[/bold] or [bold]/help[/bold] [dim]to view all commands"
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


def print_history(context: list[dict]) -> None:
    """Replay the conversation history into the terminal."""
    from rich.markdown import Markdown
    from rich.panel import Panel

    for msg in context:
        role = msg.get("role")

        if role == "user":
            content = msg.get("content") or ""
            for line in content.splitlines():
                console.print(f"> {line}".ljust(console.width), style=COLORS["user_input"])
            console.print()
            console.print(Rule(style="dim"))

        elif role == "assistant":
            content = msg.get("content") or ""
            # Strip horizontal rules from saved content — old sessions may have them
            content = re.sub(r'^[ \t]*[-*_]{3,}\s*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'^[ \t]*(-\s+){2,}-?\s*$', '', content, flags=re.MULTILINE)
            if content:
                parts = re.split(r"(```[\s\S]*?```)", content)
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

            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    try:
                        parsed = json.loads(args)
                        flat = ", ".join(f"{k}={v}" for k, v in parsed.items())
                    except (json.JSONDecodeError, TypeError):
                        flat = args
                    if len(flat) > console.width - 14:
                        flat = flat[:console.width - 18] + "..."
                    console.print(f"   [{COLORS['accent']}]{name}:[/{COLORS['accent']}] {flat}")
                console.print()
                console.print()

        elif role == "tool":
            content = msg.get("content") or ""
            if content:
                if len(content) > 200:
                    content = content[:200] + "..."
                console.print(f"   tool result: {content}", style="dim")

    console.print(Rule(style="bold green"))
    console.print(f"   [bold]End of history \u2014 {len(context)} messages loaded[/bold]")
    console.print()