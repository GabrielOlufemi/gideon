from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import get_agent_name

AGENT_NAME = get_agent_name()

COLORS = {
    "user_input" : "on grey19",
    "accent" : "dark_orange",
    "tool_detail" : "dim",
    "reply" : "default",
    "error" : "red"
}

console = Console()

def print_user(message: str) -> None:
    print("\033[F\033[K", end="")
    console.print(f"> {message}".ljust(console.width), style=COLORS["user_input"])
       
def print_tool(message: str) -> None:
    console.print(f"   {message}", style=COLORS["tool_detail"])

def print_reply(message: str) -> None:
    console.print(Markdown(message), style=COLORS["reply"])

def print_error(message: str) -> None:
    console.print(message, style=COLORS["error"])

def print_permission(name: str, details: str) -> None:
    console.print(Panel(
        details,
        title=f"{AGENT_NAME} wants to run '{name}'",
        border_style=COLORS['accent'],
        expand=True
    ))