from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import FeatureType
from agent.jobs.spells import AttackSpell
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType

Mage = CharacterJob(
    name="Mage",
    hit_die=6,
    primary_stat=StatType.INT,
    save_proficiencies=[StatType.INT, StatType.WIS],
    weapon_proficiencies=[],
    features=[
        JobFeature(
            ref_id=FeatureId.SPELL_SAVE_ADVANTAGE,
            name="Spellcasting",
            description="Gain ability to cast spells using INT.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"stat": StatType.INT},
        ),
        JobFeature(
            ref_id=FeatureId.ARCANE_RECOVERY,
            name="Arcane Recovery",
            description="Once per combat, you can recover some expended spell slots.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
        JobFeature(
            ref_id=FeatureId.AC_BONUS_WITHOUT_ARMOR,
            name="Mage Armor",
            description="+3 to AC while not wearing armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"value": 3},
        ),
    ],
    spells=[
        AttackSpell(
            ref_id=FeatureId.MAGIC_MISSILE,
            name="Magic Missile",
            description="Automatically hits and deals 1d4+1 force damage per missile.",
            level_required=1,
            type=FeatureType.ACTIVE,
            is_aoe=False,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.MULTI,
            range=10,
            hits=3,
            damage_dice="1d4+1",
            damage_type=DamageType.FORCE,
            requires_save=False,
        ),
    ],
)
