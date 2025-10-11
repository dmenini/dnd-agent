import random
import re

from agent.models.state import DiceRoll

dice_pattern = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


class DiceRoller:
    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)  # noqa: S311

    def roll_once(self, expr: str) -> DiceRoll:
        n, sides, mod = self._parse_expression(expr)
        rolls = [self.random.randint(1, sides) for _ in range(n)]
        return DiceRoll(
            expression=expr,
            rolls=rolls,
            total=sum(rolls) + mod,
            raw=sum(rolls),
        )

    def sides(self, expr: str) -> int:
        _, sides, _ = self._parse_expression(expr)
        return sides

    def _parse_expression(self, expr: str) -> tuple[int, int, int]:
        match = dice_pattern.match(expr.strip())
        if not match:
            msg = f"Invalid dice expression: {expr}"
            raise ValueError(msg)

        n = int(match.group(1) or 1)
        sides = int(match.group(2))
        mod = int(match.group(3) or 0)
        return n, sides, mod

    def roll_with_context(self, *, dice_expression: str, advantage: bool | None = None) -> DiceRoll:
        # Normal roll
        roll1 = self.roll_once(dice_expression)

        if advantage is None:
            return roll1

        # Advantage/disadvantage: roll twice
        roll2 = self.roll_once(dice_expression)

        chosen = (
            roll1
            if (advantage and roll1.total >= roll2.total) or (not advantage and roll1.total <= roll2.total)
            else roll2
        )
        chosen.expression += " (adv)" if advantage else " (dis)"
        return chosen
