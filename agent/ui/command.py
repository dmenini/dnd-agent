from textual.message import Message
from textual.widgets import Input


class CommandInput(Input):
    """Bottom input field for player commands."""

    class CommandEntered(Message):
        def __init__(self, sender: "CommandInput", command: str) -> None:
            super().__init__()
            self.command = command

    def on_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses Enter."""
        command = event.value.strip()
        if command:
            # Send message upward to the parent App
            self.post_message(self.CommandEntered(self, command))
        self.value = ""  # clear input field
