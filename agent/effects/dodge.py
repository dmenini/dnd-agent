from __future__ import annotations

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import AttackerDisadvantageOnAttackRoll, Trait


class Dodge(StatusEffect):
    """
    * Attack rolls against the target have disadvantage.
    """

    type: EffectType = EffectType.DODGING
    _traits: list[Trait] = [AttackerDisadvantageOnAttackRoll()]
