from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.status_effects.blessed import Blessed
from agent.equipment.armor import ArmorType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.jobs.spells import AttackSpell, HealingSpell, SupportSpell
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType

Cleric = CharacterJob(
    type=JobType.CLERIC,
    hit_die=8,
    primary_stat=StatType.WIS,
    save_proficiencies=[StatType.WIS, StatType.CHA],
    weapon_proficiencies=[],
    features=[
        JobFeature(
            ref_id=FeatureId.SPELL_SAVE_ADVANTAGE,
            name="Spellcasting",
            description="Gain ability to cast spells using WIS.",
            level_required=1,
            type=FeatureType.PASSIVE,
        ),
        JobFeature(
            ref_id=FeatureId.DIVINE_RESTORATION,
            name="Channel Divinity - Restore Vitality",
            description="Once per combat, channel divine power to heal allies.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
        JobFeature(
            ref_id=FeatureId.AC_BONUS_WITH_ARMOR_TYPES,
            name="Blessed Armor",
            description="+1 to AC while wearing light or medium armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"value": 1, "armor_types": [ArmorType.LIGHT, ArmorType.MEDIUM]},
        ),
    ],
    spells=[
        AttackSpell(
            ref_id=FeatureId.SACRED_FLAME,
            name="Sacred Flame",
            description="Call down radiant fire to deal 1d8 radiant damage. Target makes a DEX save for no damage.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.SINGLE,
            range=12,
            damage_dice="1d8",
            damage_type=DamageType.RADIANT,
            requires_save=True,
            stat=StatType.DEX,
        ),
        HealingSpell(
            ref_id=FeatureId.CURE_WOUNDS,
            name="Cure Wounds",
            description="Touch a creature to restore 1d8 + WIS modifier hit points.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.SINGLE,
            range=1,
            heal_dice="1d8",
        ),
        SupportSpell(
            ref_id=FeatureId.BLESS,
            name="Bless",
            description="Up to three allies gain +1d4 to attack rolls and saving throws.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.MULTI,
            range=9,
            hits=3,
            effects=[Blessed(duration=1)],
        ),
    ],
)
