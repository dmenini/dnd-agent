from agent.actions.base import ActionCategory
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.equipment.base import Equipment
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class Spell(Equipment):
    stat: StatType = StatType.INT
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD
    targeting: TargetingType


class AttackSpell(Spell):
    stat: StatType = StatType.INT
    damage_dice: str
    damage_type: DamageType


class SupportSpell(Spell):
    stat: StatType = StatType.WIS
