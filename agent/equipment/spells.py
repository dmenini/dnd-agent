from agent.actions.base import ActionCategory
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.equipment.base import Equipment
from agent.models.enums import DamageType


class Spell(Equipment):
    stat: StatType = StatType.INT
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD


class AttackSpell(Spell):
    stat: StatType = StatType.INT
    damage_dice: str
    damage_type: DamageType = DamageType.MAGIC


class SupportSpell(Spell):
    stat: StatType = StatType.WIS
