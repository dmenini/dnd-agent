from abc import ABC

from pydantic import BaseModel

from agent.models.action import ActionCategory, ActionOption, ActionType, ResourceCost
from agent.models.enums import DamageType, StatType, TargetingType


class Equipment(ABC, BaseModel):
    name: str
    damage_dice: str
    damage_type: DamageType
    stat: StatType
    range: float
    description: str = ""


class Weapon(Equipment):
    name: str
    weight: float = 0.0
    magical_bonus: int = 0
    versatile: bool = False

    def to_action(self, category: ActionCategory) -> ActionOption:
        return ActionOption(
            id=f"{'off_hand' if category == ActionCategory.BONUS else 'main_hand'}_attack",
            name=f"{'Off Hand' if category == ActionCategory.BONUS else 'Main Hand'} Attack",
            source=self.name,
            action_type=ActionType.MELEE_ATTACK,
            category=category,
            targeting=TargetingType.SINGLE,
            resource_cost=ResourceCost(action_points=1),
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
            meta={"versatile": self.versatile},
        )


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR
    damage_type: DamageType = DamageType.SLASHING


class FinesseWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING


class RangeWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING
    ammo: int = 20

    def to_action(self, category: ActionCategory) -> ActionOption:
        return ActionOption(
            id="ranged_attack",
            name="Ranged Attack",
            source=self.name,
            action_type=ActionType.RANGED_ATTACK,
            category=category,
            targeting=TargetingType.SINGLE,
            resource_cost=ResourceCost(action_points=1, ammo=1),
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
        )


class Spell(Equipment):
    stat: StatType = StatType.INT
    damage_type: DamageType = DamageType.MAGIC
    mana_cost: int = 5
    cooldown: int = 0
    is_aoe: bool = False

    def to_action(self, category: ActionCategory) -> ActionOption:
        targeting = TargetingType.AREA if self.is_aoe else TargetingType.SINGLE
        return ActionOption(
            id=f"cast_{self.name.lower().replace(' ', '_')}",
            name=f"Cast {self.name}",
            source=self.name,
            action_type=ActionType.AOE_SPELL if targeting == TargetingType.AREA else ActionType.SPELL,
            category=category,
            targeting=targeting,
            resource_cost=ResourceCost(action_points=1, mana=self.mana_cost, cooldown=self.cooldown),
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
        )
