from agent.character.character import Character
from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    DisadvantageOnSavingThrow,
    HalfAttacks,
    SpeedMultiplier,
    Trait,
)


class Lethargic(StatusEffect):
    """
    * Target's movement speed is halved.
    * Target may only take half actions per turn (rounded up).
    Target may repeat the WIS saving throw with disadvantage each turn, ending the effect on a success.
    """

    type: EffectType = EffectType.LETHARGIC
    save_stat: StatType = StatType.WIS
    _traits: list[Trait] = [SpeedMultiplier(value=0.5), DisadvantageOnSavingThrow(stat=StatType.WIS), HalfAttacks()]

    def on_turn_start(self, target: Character) -> None:
        super().on_turn_start(target)
        if target.save_roll(self.save_stat).total >= self.save_dc:
            self.duration = 0
