from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import ExtraAction, Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class Hasted(StatusEffect):
    type: EffectType = EffectType.HASTED
    _traits: list[Trait] = [ExtraAction()]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
