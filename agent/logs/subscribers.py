import os

from rich.console import Console

from agent.logs.events import Event, LogLevel, Verbosity

console = Console()


def rich_printer(event: Event) -> None:
    verbosity = int(os.getenv("VERBOSITY", Verbosity.DETAIL))

    if (
        (event.type == LogLevel.DEBUG and verbosity >= Verbosity.DEBUG)
        or (event.type == LogLevel.DETAIL and verbosity >= Verbosity.DETAIL)
        or (event.type == LogLevel.MAIN and verbosity >= Verbosity.MAIN)
    ):
        console.print(event)
