import random
import re

from agent.models.state import ActionType, DiceRoll, State, TurnPhase

dice_pattern = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


class DiceRoller:
    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def roll(self, expr: str) -> DiceRoll:
        match = dice_pattern.match(expr.strip())
        if not match:
            raise ValueError(f"Invalid dice expression: {expr}")

        n = int(match.group(1) or 1)
        sides = int(match.group(2))
        mod = int(match.group(3) or 0)
        rolls = [self.random.randint(1, sides) for _ in range(n)]
        return DiceRoll(
            expression=expr,
            rolls=rolls,
            total=sum(rolls) + mod
        )

    def __call__(self, state: State) -> State:
        if state.action and state.action.action_type == ActionType.ATTACK:
            roll_result = self.roll("1d20+5")  # hardcoded for now
        else:
            roll_result = DiceRoll(expression="", rolls=[], total=0)
        state.roll = roll_result
        state.phase = TurnPhase.EXECUTE
        return state
