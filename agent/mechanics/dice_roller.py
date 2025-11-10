import random
import re

from pydantic import BaseModel

dice_pattern = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


class DiceRoll(BaseModel):
    expression: str
    rolls: list[int]
    total: int
    raw: int
    advantage: bool | None = None


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

    def roll_twice(self, expr: str) -> DiceRoll:
        n, sides, mod = self._parse_expression(expr)
        rolls = [self.random.randint(1, sides) for _ in range(n * 2)]
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
        if advantage is None:
            return self.roll_once(dice_expression)

        # Advantage/disadvantage: roll twice
        roll = self.roll_twice(dice_expression)
        chosen = max(roll.rolls) if advantage else min(roll.rolls)
        mod = roll.total - roll.raw

        return DiceRoll(
            expression=dice_expression + " (adv)" if advantage else " (dis)",
            rolls=roll.rolls,
            raw=roll.raw,
            total=chosen + mod,
            advantage=advantage,
        )
