from typing import Any

from textual.reactive import reactive
from textual.widgets import DataTable

from agent.actions.base import Action, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.damage import DamageEffect
from agent.ui.widgets.action_modal import ActionInfoModal


class ActionsSummaryTable(DataTable):
    """A compact summary table of all actions with minimal info."""

    actions: reactive[dict[str, Action]] = reactive(dict, init=False)

    def __init__(self, actions: list[Action] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.actions = {a.id: a for a in (actions or [])}

    def on_mount(self) -> None:
        """Setup columns after mounting."""
        self._setup_columns()
        self._populate_rows()

    def _setup_columns(self) -> None:
        """Define consistent columns."""
        if len(self.columns) > 0:
            return  # Columns already set up

        columns = [
            "Name",
            "Category",
            "Range",
            "Targeting",
            "Info",
        ]
        for name in columns:
            self.add_column(name)

    def watch_actions(self) -> None:
        """Called automatically when actions changes."""
        if self.is_mounted:
            self._populate_rows()

    def _populate_rows(self) -> None:
        """Populate table rows with action data."""
        # Clear existing rows
        self.clear()

        # Add rows for each action
        for a in sorted(self.actions.values(), key=lambda x: x.name):
            self.add_row(
                f"[bold]{a.name}[/bold]",
                a.category.value,
                f"{a.range} m",
                a.targeting.value,
                self._info_for_action(a),
                key=a.id,
            )

    def update_actions(self, actions: list[Action]) -> None:
        """Update the table with new actions."""
        self.actions = {a.id: a for a in actions}  # Triggers watch_actions

    def _info_for_action(self, action: Action) -> str:
        """Build the info field dynamically depending on subclass."""
        info = ""

        if isinstance(action, ComposableAction):
            # Check if it's a spell with level metadata
            if action.type == ActionType.CAST_SPELL and "spell_level" in action.metadata:
                level_info = f"Lv {action.metadata['spell_level']}"

                # Check if it has damage effects
                damage_effects = [e for e in action.effects if isinstance(e, DamageEffect)]
                if damage_effects:
                    damage = damage_effects[0]
                    info = (
                        f"{level_info}, {action.hits} hit(s) for {damage.damage_dice} {damage.damage_type.value} damage"
                    )
                else:
                    info = level_info
            # Check if it has damage effects (attacks)
            else:
                damage_effects = [e for e in action.effects if isinstance(e, DamageEffect)]
                if damage_effects:
                    damage = damage_effects[0]
                    info = f"{action.hits} hit(s) for {damage.damage_dice} {damage.damage_type.value} damage"
                elif hasattr(action, "hits"):
                    info = f"{action.hits} hit(s)"

        elif hasattr(action, "status_effects"):
            eff = ", ".join(e.type.value for e in action.status_effects)
            info += f" (+ {eff})"

        return info or "-"

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Open a modal when a cell is clicked."""
        action_id = event.cell_key.row_key.value
        action = self.actions.get(action_id or "")
        if action:
            self.app.push_screen(ActionInfoModal(action))
