import os
from typing import Any

from rich.console import Console

from agent.logs.events import Event, LogLevel, Verbosity

console = Console()


def rich_printer(event: Event) -> None:
    verbosity = int(os.getenv("VERBOSITY", Verbosity.DETAIL))
    always_log = {LogLevel.MAIN, LogLevel.MAP, LogLevel.HEADER, LogLevel.SYSTEM}

    if (
        (event.type == LogLevel.DEBUG and verbosity >= Verbosity.DEBUG)
        or (event.type == LogLevel.DETAIL and verbosity >= Verbosity.DETAIL)
        or (event.type in always_log)
    ):
        # console.print(event)
        pass


def rich_printer_plain(element: Any) -> None:
    console.print(element)
