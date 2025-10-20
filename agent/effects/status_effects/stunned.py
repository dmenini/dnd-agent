from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import AttackerAdvantageOnAttackRoll, CannotAct, CannotMove, FailOnSavingThrow, Trait


class Stunned(StatusEffect):
    """
    * Target can't take actions or reactions (incapacitated).
    * Target can't move.
    * Target can speak only falteringly. -> Not yet implemented
    * Target automatically fails Strength and Dexterity saving throws.
    * Attack rolls against the creature have advantage.
    """

    type: EffectType = EffectType.STUNNED
    _traits: list[Trait] = [
        CannotAct(),
        CannotMove(),
        AttackerAdvantageOnAttackRoll(),
        FailOnSavingThrow(stat=StatType.STR),
        FailOnSavingThrow(stat=StatType.DEX),
    ]
