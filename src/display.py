from rich.console import Console
from rich.panel import Panel
from rich.box import Box
from rich.padding import Padding
from rich.markdown import Markdown
from rich.table import Table
from rich import box

from config import get_agent_name

AGENT_NAME = get_agent_name()
VERSION = "0.1.0"


COLORS = {
    "user_input": "on grey19",
    "accent": "#55821A",
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


def print_user(message: str) -> None:
    print("\033[F\033[K", end="")
    console.print(f"> {message}".ljust(console.width), style=COLORS["user_input"])
    console.print()

def print_tool(message: str) -> None:
    console.print(f"   {message}", style=COLORS["tool_detail"])


def print_reply(message: str) -> None:
    console.print(Padding(
        Panel(
            Markdown(message),
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
            expand=False,
            padding=(0, 1),
        ),
        INDENT,
    ))
    console.print()


# welcome stuff

def print_welcome(cwd: str) -> None:
    left = (
        "[bold]Welcome to Gideon[/bold]\n"
        f"[dim]{cwd}[/dim]\n"
        "No model selected yet"
    )

    right = (
        "[bold]Setup[/bold]\n"
        "1. Choose a model\n"
        "2. Add your OpenRouter key\n"
        "[bold]Who is Gideon?[/bold] Hey, I'm Gideon, gabriel's alter ego (sort of) and "
        "your terminal coding agent. Point me at a problem and I'll get "
        "poke through your code, run commands and doing the heavy lifting while you sit back and relax."
        " I'll just check with you first before doing anything permanent."
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