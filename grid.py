# chess_grid.py
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Grid

BOARD_SIZE = 8


class Cell(Static):
    """A single square cell."""

    def __init__(self, coord: str, is_light: bool):
        super().__init__(coord)
        self.coord = coord
        self.classes = "cell light" if is_light else "cell dark"


class ChessBoard(Grid):
    """The 8×8 chess board."""

    def compose(self) -> ComposeResult:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                coord = f"{chr(ord('a') + c)}{BOARD_SIZE - r}"
                is_light = (r + c) % 2 == 0
                yield Cell(coord, is_light)


class ChessApp(App):
    """Textual app displaying a chess-like grid."""

    CSS = """
    Screen {
        align: center middle;
        background: black;
    }

    ChessBoard {
        grid-size: 8;
        grid-gutter: 0;
        width: 80w;
        height: 80h;
    }

    .cell {
        text-align: center;
        width: 1fr;
        height: 1fr;
        border: none;
    }

    .light {
        background: rgb(240,217,181);
        color: black;
    }

    .dark {
        background: rgb(181,136,99);
        color: white;
    }
    """

    def compose(self) -> ComposeResult:
        yield ChessBoard()


if __name__ == "__main__":
    ChessApp().run()
