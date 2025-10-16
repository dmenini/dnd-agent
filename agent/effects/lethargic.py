from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    DisadvantageOnSavingThrow,
    HalfActions,
    SpeedMultiplier,
    Trait,
)

if TYPE_CHECKING:
    from agent.character.character import Character


class Lethargic(StatusEffect):
    """
    * Target's movement speed is halved.
    * Target may only take half actions per turn (rounded up).
    Target may repeat the WIS saving throw with disadvantage each turn, ending the effect on a success.
    """

    type: EffectType = EffectType.LETHARGIC
    save_stat: StatType = StatType.WIS
    _traits: list[Trait] = [SpeedMultiplier(value=0.5), DisadvantageOnSavingThrow(stat=StatType.WIS), HalfActions()]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        if target.save_roll(self.save_stat).total >= self.save_dc:
            self.duration = 0
        else:
            self.duration -= 1
