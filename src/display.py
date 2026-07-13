from rich.console import Console
from rich.panel import Panel


COLORS = {
    "user_input" : "on grey19",
    "accent" : "dark_orange",
    "tool_detail" : "dim",
    "reply" : "default",
    "error" : "red"
}

console = Console()

def print_user(message: str) -> None:
    console.print(message, style=COLORS["user_input"])

def print_tool(message: str) -> None:
    console.print(message, style=COLORS["tool_detail"])

def print_reply(message: str) -> None:
    for line in message.splitlines():
            console.print(f"[{COLORS['accent']}]│[/{COLORS['accent']}] {line}")

def print_error(message: str) -> None:
    console.print(message, style=COLORS["error"])

def print_permission(name: str, details: str, options: str) -> None:
    console.print(Panel(
        f"{details}\n\n{options}",
        title=f"Eureka wants to run '{name}'",
        border_style=COLORS['accent']
    ))