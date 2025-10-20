from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, FeatureType, JobFeature
from agent.jobs.features import FeatureId

Mage = CharacterJob(
    name="Mage",
    hit_die=6,
    primary_stat=StatType.INT,
    save_proficiencies=[StatType.INT, StatType.WIS],
    features=[
        JobFeature(
            reference_id=FeatureId.SPELL_SAVE_ADVANTAGE,
            name="Spellcasting",
            description="Gain ability to cast spells using INT.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"stat": StatType.INT},
        ),
        JobFeature(
            reference_id=FeatureId.ARCANE_RECOVERY,
            name="Arcane Recovery",
            description="Once per combat, you can recover some expended spell slots.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
        JobFeature(
            reference_id=FeatureId.AC_BONUS_WITHOUT_ARMOR,
            name="Mage Armor",
            description="+3 to AC while not wearing armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"value": 3},
        ),
    ],
)
