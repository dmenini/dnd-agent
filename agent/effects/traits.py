from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import Modifier
from agent.models.enums import DamageType

if TYPE_CHECKING:
    from agent.character.character import Character

MELEE_RANGE = 5


class Trait:
    def on_expire(self, target: Character) -> None:
        target.remove_modifier(str(id(self)))


class AttackerDisadvantageOnAttackRoll(Trait):
    ATTR = "defense_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.ATTR, value=-1, operation="add"))


class AttackerAdvantageOnAttackRoll(Trait):
    ATTR = "defense_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.ATTR, value=+1, operation="add"))


class TargetDisadvantageOnAttackRoll(Trait):
    ATTR = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.ATTR, value=-1, operation="add"))


class TargetAdvantageOnAttackRoll(Trait):
    ATTR = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.ATTR, value=+1, operation="add"))


class DisadvantageOnDexSavingThrow(Trait):
    ATTR = "dex_save_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.ATTR, value=-1, operation="add"))


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
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False  # Cannot move


class CannotAct(Trait):
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.standard_actions = -1
        target.action_economy.bonus_actions = -1
        target.action_economy.reaction_available = False


class ExtraAction(Trait):
    def on_turn_start(self, target: Character) -> None:
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += 1
