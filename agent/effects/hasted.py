from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.lethargic import Lethargic
from agent.effects.traits import ACBonus, AdvantageOnSavingThrow, ExtraAction, SpeedBonus, Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class Hasted(StatusEffect):
    """
    The target's speed is doubled, it gains a +2 bonus to AC, it has advantage
    on Dexterity saving throws, and it gains an additional action on each of its turns.
    When the effect ends, the target gets lethargy for 1 turn.
    """

    type: EffectType = EffectType.HASTED
    _traits: list[Trait] = [
        ExtraAction(),
        SpeedBonus(mult=2),
        ACBonus(val=2),
        AdvantageOnSavingThrow(stat=StatType.DEX),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1

    def on_expire(self, target: Character) -> None:
        super().on_expire(target)
        Lethargic(duration=1).try_apply(target)
