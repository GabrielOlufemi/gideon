from rich.console import Console
from rich.panel import Panel
from rich.box import Box
from rich.padding import Padding
from rich.markdown import Markdown

from config import get_agent_name

AGENT_NAME = get_agent_name()

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

from rich.table import Table

# placeholder gif for now
GLYPH = """\
  ▄▄▄▄▄▄
 █      
 █  ▄▄▄▄
 █     █
 █     █
  ▀▀▀▀▀▀"""


def print_welcome() -> None:
    left = f"[{COLORS['accent']}]{GLYPH}[/{COLORS['accent']}]"

    right = (
        "[bold]Setup[/bold]\n"
        "1. Choose a model\n"
        "2. Add your OpenRouter key"
    )

    layout = Table.grid(padding=(0, 3))
    layout.add_column()
    layout.add_column()
    layout.add_row(left, right)

    console.print()
    console.print(Padding(
        Panel(
            layout,
            title="Gideon",
            title_align="left",
            border_style=COLORS["accent"],
            expand=False,
            padding=(1, 2),
        ),
        INDENT,
    ))
    console.print()