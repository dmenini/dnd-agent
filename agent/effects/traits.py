from __future__ import annotations

from typing import TYPE_CHECKING

from agent.models.enums import DamageType, StatType

if TYPE_CHECKING:
    from agent.models.character import Character

MELEE_RANGE = 5


class Trait:
    pass


class AttackerDisadvantageOnAttackRoll(Trait):
    def on_attack_roll_as_actor(self) -> bool:
        return False


class AttackerAdvantageOnAttackRoll(Trait):
    def on_attack_roll_as_actor(self) -> bool:
        return True


class TargetDisadvantageOnAttackRoll(Trait):
    def on_attack_roll_as_target(self) -> bool:
        return False


class TargetAdvantageOnAttackRoll(Trait):
    def on_attack_roll_as_target(self) -> bool:
        return True


class DisadvantageOnDexSavingThrow(Trait):
    def on_save_roll(self, stat: StatType) -> bool | None:
        return False if stat == StatType.DEX else None


class AutoCritIfMelee(Trait):
    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        return actor.distance(target.pos) <= MELEE_RANGE


class DamageOverTime(Trait):
    def __init__(self, damage: int, dtype: DamageType) -> None:
        self.damage = damage
        self.dtype = dtype

    def on_turn_end(self, target: Character) -> None:
        target.apply_damage(damage=self.damage, damage_type=self.dtype)


class CannotMove(Trait):
    """Target cannot move."""

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False  # Cannot move


class CannotAct(Trait):
    """Target cannot act."""

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.standard_actions = -1  # Cannot act
        target.action_economy.bonus_actions = -1  # Cannot act
        target.action_economy.reaction_available = False


class ExtraAction(Trait):
    """Grant an extra action."""

    def on_turn_start(self, target: Character) -> None:
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += 1
