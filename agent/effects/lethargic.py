from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    DisadvantageOnSavingThrow,
    HalveActions,
    SpeedBonus,
    Trait,
)

if TYPE_CHECKING:
    from agent.character.character import Character


class Lethargic(StatusEffect):
    """
    Movement speed is halved, and if they can make multiple attacks they may only take
    half that many attacks per turn (rounded up). They may repeat the saving throw with disadvantage
    each turn, ending the effect on a success.
    """

    type: EffectType = EffectType.LETHARGIC
    save_stat: StatType = StatType.WIS
    _traits: list[Trait] = [SpeedBonus(mult=0.5), DisadvantageOnSavingThrow(stat=StatType.WIS), HalveActions()]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        if target.save_roll(self.save_stat).total >= self.save_dc:
            self.duration = 0
        else:
            self.duration -= 1
