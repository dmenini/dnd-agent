from agent.mechanics.dice_roller import DiceRoller
from agent.models.state import State


class StartCombatNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        state.append_log("Starting combat!")

        rolls = []
        for cid, char in state.characters.items():
            expr = f"1d20+{char.stats.modifier('dexterity')}"
            init_roll = self.dice.roll_with_context(dice_expression=expr)
            rolls.append((init_roll.total, cid))
            state.append_log(f"{char.name} rolls initiative: {init_roll.total}")

        state.turn_order = [cid for _, cid in sorted(rolls, reverse=True)]
        state.turn_index = 0
        state.append_log("Initiative order: " + " → ".join(state.characters[cid].name for cid in state.turn_order))

        state.flush_logs()

        return state
