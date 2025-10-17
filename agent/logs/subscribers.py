from rich import Console
from rich.style import Style
from rich.text import Text

from agent.logs.events import Event

console = Console()


def rich_printer(event: Event) -> None:
    color = {
        "system": Style(color="yellow"),
        "map": Style(),
        "actor": Style(color="green"),
    }
    text = Text(str(event), style=color[event.type])
    console.print(text)
