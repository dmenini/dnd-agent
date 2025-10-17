from rich.console import Console

from agent.logs.events import Event

console = Console()


def rich_printer(event: Event) -> None:
    console.print(event)
