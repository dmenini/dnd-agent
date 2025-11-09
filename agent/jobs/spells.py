from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from agent.actions.base import ActionCategory
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.status_effects.base import StatusEffect
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class SpellType(str, Enum):
    ATTACK = "attack"
    SUPPORT = "support"


class SpellBase(JobFeature):
    type: FeatureType = FeatureType.SPELL
    spell_type: SpellType
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD
    targeting: TargetingType
    range: float
    stat: StatType | None = None  # Default to spellcaster stat if not specified


class AttackSpell(SpellBase):
    spell_type: Literal[SpellType.ATTACK] = Field(default=SpellType.ATTACK, frozen=True)
    damage_dice: str
    damage_type: DamageType
    hits: int = 1
    requires_save: bool = True


class SupportSpell(SpellBase):
    spell_type: Literal[SpellType.SUPPORT] = Field(default=SpellType.SUPPORT, frozen=True)
    effects: list[StatusEffect] = []
    hits: int = 1


Spell: TypeAlias = Annotated[  # noqa: UP040
    AttackSpell | SupportSpell,
    Field(discriminator="spell_type"),
]
