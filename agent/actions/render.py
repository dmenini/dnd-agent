from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent.actions.base import Action
from agent.actions.common.attack import AttackAction
from agent.actions.common.spell import AttackSpellAction, SupportSpellAction


def render_action(action: Action, max_width: int = 50) -> Panel:
    """Render a single Action or subclass as a formatted Rich panel."""

    header = f"[bold cyan]{action.name}[/bold cyan]"
    desc = Text(action.description + "\n", style="white")

    # Base info table
    table = Table.grid(expand=False, padding=(0, 1, 0, 2))  # top, right, bottom, left
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    table.add_row("ID", str(action.id))
    table.add_row("Type", str(action.type.value))
    table.add_row("Category", str(action.category.value))
    table.add_row("Targeting", str(action.targeting.value))
    table.add_row("Hits", str(action.hits))
    table.add_row("Range", f"{action.range} m")

    damage = getattr(action, "damage_dice", None)
    damage_type = getattr(action, "damage_type", None)
    table.add_row("Damage", f"{damage} {damage_type.value}" if damage else "-")

    stat = getattr(action, "stat", None)
    table.add_row("Stat", stat.value if stat else "-")

    effects = ", ".join([e.type.value for e in getattr(action, "status_effects", [])]) or "-"
    table.add_row("Effects", effects)

    level = getattr(action, "level", None)
    table.add_row("Spell Level", f"Level {level.value}" if level else "-")

    # Group description + table
    content = Group(desc, table)

    return Panel(
        content,
        title=header,
        border_style="bright_blue",
        padding=(1, 2),
        expand=False,
        width=max_width,
    )


def render_actions_grid(actions: list[Action], max_width: int = 50) -> Columns:
    """Render multiple actions in a grid-like layout."""
    panels = [render_action(a, max_width=max_width) for a in actions]
    return Columns(panels, equal=True, expand=True, align="center")


def render_actions_summary(actions: list[Action]) -> Table:
    """Render a compact summary table of all actions with minimal info."""
    table = Table(
        expand=True,
        show_lines=False,
        header_style="bold cyan",
        box=box.MINIMAL,
    )

    # Define consistent columns
    table.add_column("ID", style="yellow", no_wrap=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="dim", no_wrap=True)
    table.add_column("Range", justify="right", style="white")
    table.add_column("Targeting", justify="right", style="white")
    table.add_column("Info", style="white")

    for action in sorted(actions, key=lambda a: a.name):
        # Build info field dynamically depending on subclass
        if isinstance(action, AttackAction):
            info = f"{action.hits} hit(s) for {action.damage_dice} {action.damage_type.value} damage"
            if action.status_effects:
                effects = ", ".join(e.type.value for e in action.status_effects)
                info += f" (+ {effects})"
        elif isinstance(action, AttackSpellAction):
            info = f"Lv {action.level.value}, "
            info += f"{action.hits} hit(s) for {action.damage_dice} {action.damage_type.value} damage"
        elif isinstance(action, SupportSpellAction):
            info = f"Lv {action.level.value}"
            if action.status_effects:
                effects = ", ".join(e.type.value for e in action.status_effects)
                info += f" (+ {effects})"
        else:
            info = "-"

        table.add_row(
            action.id,
            f"[bold]{action.name}[/bold]",
            action.category.value,
            f"{action.range} m",
            f"{action.targeting.value}",
            info,
        )

    return table
