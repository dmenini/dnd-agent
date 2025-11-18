from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from agent.actions.base import ActionCategory
from agent.actions.common.evocation import EvocationSpellAction
from agent.actions.common.spell import AttackSpellAction, HealingSpellAction, SupportSpellAction
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.effects.evocations.base import Evocation
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.status_effects.collection import Blessed
from agent.jobs.feature import JobFeature
from agent.models.constants import TOUCH_RANGE
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType


class SpellType(str, Enum):
    ATTACK = "attack"
    SUPPORT = "support"
    HEALING = "healing"
    EVOCATION = "evocation"


class SpellBase(JobFeature):
    spell_type: SpellType
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD
    targeting: TargetingType
    range: float
    ability: AbilityType | None = None  # Default to spellcaster ability if not specified


class AttackSpell(SpellBase):
    spell_type: Literal[SpellType.ATTACK] = Field(default=SpellType.ATTACK, frozen=True)
    damage_dice: str
    damage_type: DamageType
    hits: int = 1
    requires_save: bool = True


class SupportSpell(SpellBase):
    spell_type: Literal[SpellType.SUPPORT] = Field(default=SpellType.SUPPORT, frozen=True)
    apply_conditions: list[StatusEffect] = []
    remove_conditions: list[StatusType] = []
    hits: int = 1


class HealingSpell(SpellBase):
    spell_type: Literal[SpellType.HEALING] = Field(default=SpellType.HEALING, frozen=True)
    heal_dice: str


class EvocationSpell(SpellBase):
    spell_type: Literal[SpellType.EVOCATION] = Field(default=SpellType.EVOCATION, frozen=True)
    evocation: Evocation


Spell: TypeAlias = Annotated[  # noqa: UP040
    AttackSpell | SupportSpell | HealingSpell | EvocationSpell,
    Field(discriminator="spell_type"),
]

spell_action_map = {
    SpellType.ATTACK: AttackSpellAction,
    SpellType.SUPPORT: SupportSpellAction,
    SpellType.HEALING: HealingSpellAction,
    SpellType.EVOCATION: EvocationSpellAction,
}


class SpellBuilder:
    @staticmethod
    def cure_wounds(level_required: int) -> HealingSpell:
        # TODO: When you cast this spell using a spell slot of 2nd level or higher,
        #  the Healing increases by 1d8 for each slot level above 1st.
        return HealingSpell(
            ref_id=FeatureId.CURE_WOUNDS,
            name="Cure Wounds",
            description=(
                "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier."
            ),
            level_required=level_required,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.SINGLE,
            range=TOUCH_RANGE,
            heal_dice="1d8",
        )

    @staticmethod
    def bless(level_required: int) -> SupportSpell:
        # TODO: When you cast this spell using a spell slot of 2nd level or higher,
        #  you can target one additional creature for each slot level above 1st.
        return SupportSpell(
            ref_id=FeatureId.BLESS,
            name="Bless",
            description=(
                "You bless up to three creatures of your choice within range. "
                "Whenever a target makes an attack roll or a saving throw before the spell ends, "
                "the target can roll a d4 and add the number rolled to the attack roll or saving throw."
            ),
            level_required=level_required,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.ALLIES,
            range=30,
            hits=3,
            apply_conditions=[Blessed.with_duration(1)],
        )

    @staticmethod
    def lesser_restoration(level_required: int) -> SupportSpell:
        return SupportSpell(
            ref_id=FeatureId.LESSER_RESTORATION,
            name="Lesser Restoration",
            description=(
                "You touch a creature and can end either one disease or one condition afflicting it. "
                "The condition can be blinded, deafened, paralyzed, or poisoned."
            ),
            level_required=level_required,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.ALLIES,
            range=TOUCH_RANGE,
            # We only remove the first match, so sort by priority
            remove_conditions=[StatusType.PARALYZED, StatusType.POISONED, StatusType.BLINDED, StatusType.DEAFENED],
        )

    @staticmethod
    def spiritual_sword(level_required: int) -> EvocationSpell:
        attack = JobFeature(
            ref_id=FeatureId.MELEE_SPELL_ATTACK,
            name="Spiritual Weapon Attack",
            description="As a bonus action on your turn, you can move the weapon and attack the nearest creature.",
            kwargs={
                "range": 20,
                "damage_dice": "1d8",
                "damage_type": DamageType.FORCE,
            },
        )
        evo = Evocation(
            source_id=FeatureId.SPIRITUAL_SWORD.value,
            name="Spiritual Sword",
            duration=10,
            features=[attack],
            on_cast_use=attack.ref_id,
        )
        return EvocationSpell(
            ref_id=FeatureId.SPIRITUAL_SWORD,
            level_required=level_required,
            name="Spiritual Sword",
            description=(
                "You create a floating, spectral weapon within range that lasts for the duration. "
                "When you cast the spell, you can make a melee spell attack against a creature within weapon range. "
                "On a hit, the target takes force damage equal to 1d8 + your spellcasting ability modifier."
            ),
            targeting=TargetingType.SINGLE,
            range=20,
            evocation=evo,
        )
