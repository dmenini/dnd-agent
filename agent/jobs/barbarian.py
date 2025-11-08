from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.enums import FeatureId

Barbarian = CharacterJob(
    type=JobType.BARBARIAN,
    hit_die=12,
    primary_stat=StatType.STR,
    save_proficiencies=[StatType.STR, StatType.CON],
    weapon_proficiencies=[],
    features=[
        JobFeature(
            ref_id=FeatureId.RAGE,
            name="Rage",
            description="Enter a rage as a bonus action to gain advantage on STR checks and bonus melee damage.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=2,
            kwargs={"damage_bonus": 2},
        ),
        JobFeature(
            ref_id=FeatureId.UNARMORED_DEFENSE,
            name="Unarmored Defense",
            description="While not wearing armor, AC = 10 + DEX + CON modifier.",
            level_required=1,
            type=FeatureType.PASSIVE,
        ),
    ],
)
