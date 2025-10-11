from agent.mechanics.dice_roller import DiceRoller
from agent.models.state import ActionType, DiceRoll, State


class DiceRollerNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        attack_actions = {ActionType.ATTACK, ActionType.CAST_SPELL, ActionType.SHOOT}
        if state.action and state.action.action_type in attack_actions:
            character = state.characters[state.actor_id]

            stat = character.stats.get_stat_from_action(state.action.action_type)
            mod = character.stats.modifier(stat)
            advantage = character.stats.advantage(stat)
            expr = state.action.dice_expression + (f"+{mod}" if mod >= 0 else f"-{mod}")

            roll_result = self.dice.roll_with_context(dice_expression=expr, advantage=advantage)

        else:
            roll_result = DiceRoll(expression="", rolls=[], total=0, raw=0)

        state.roll = roll_result
        return state
