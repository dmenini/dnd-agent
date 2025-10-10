import random
import re

from agent.models.character import Character
from agent.models.state import Action, ActionType, DiceRoll, State

dice_pattern = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


class DiceRoller:
    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)  # noqa: S311

    def roll_once(self, n: int, sides: int, mod: int) -> DiceRoll:
        rolls = [self.random.randint(1, sides) for _ in range(n)]
        return DiceRoll(
            expression=f"{n}d{sides}{'+' if mod >= 0 else ''}{mod}",
            rolls=rolls,
            total=sum(rolls) + mod,
        )

    def _parse_expression(self, expr: str) -> tuple[int, int]:
        match = dice_pattern.match(expr.strip())
        if not match:
            msg = f"Invalid dice expression: {expr}"
            raise ValueError(msg)

        n = int(match.group(1) or 1)
        sides = int(match.group(2))
        return n, sides

    def _get_relevant_stat(self, action: Action) -> str | None:
        if action.action_type == ActionType.ATTACK:
            return "strength"
        if action.action_type == ActionType.SHOOT:
            return "dexterity"
        if action.action_type == ActionType.CAST_SPELL:
            return "intelligence"
        if action.action_type == ActionType.ROLEPLAY:
            return "charisma"
        return None

    def roll_with_context(self, character: Character, action: Action) -> DiceRoll:
        n, sides = self._parse_expression(action.dice_expression)

        stat_name = self._get_relevant_stat(action)
        if stat_name:
            stat_value = getattr(character.stats, stat_name)
            mod = character.stats.modifier(stat_name)
            advantage = character.stats.advantage(stat_value)
        else:
            mod = 0
            advantage = 0

        # Normal roll
        roll1 = self.roll_once(n, sides, mod)

        if advantage == 0:
            return roll1

        # Advantage/disadvantage: roll twice
        roll2 = self.roll_once(n, sides, mod)

        chosen = (
            roll1
            if (advantage == 1 and roll1.total >= roll2.total) or (advantage == -1 and roll1.total <= roll2.total)
            else roll2
        )

        return DiceRoll(
            expression=chosen.expression + " (adv)" if advantage == 1 else " (dis)",
            rolls=[roll1.total - mod, roll2.total - mod],
            total=max(roll1.total, roll2.total) if advantage == 1 else min(roll1.total, roll2.total),
        )

    def __call__(self, state: State) -> State:
        attack_actions = {ActionType.ATTACK, ActionType.CAST_SPELL, ActionType.ROLEPLAY}
        if state.action and state.action.action_type in attack_actions:
            roll_result = self.roll_with_context(character=state.characters[state.actor_id], action=state.action)
        else:
            roll_result = DiceRoll(expression="", rolls=[], total=0)
        state.roll = roll_result
        return state
