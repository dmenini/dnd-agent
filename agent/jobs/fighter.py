from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, FeatureType, JobFeature
from agent.jobs.features import FeatureId

Fighter = CharacterJob(
    name="Fighter",
    hit_die=10,
    primary_stat=StatType.STR,
    save_proficiencies=[StatType.STR, StatType.CON],
    features=[
        JobFeature(
            reference_id=FeatureId.AC_BONUS_WITH_ARMOR,
            name="Fighting Style: Defense",
            description="+1 to AC while wearing armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
        ),
        JobFeature(
            reference_id=FeatureId.SECOND_WIND,
            name="Second Wind",
            description="Regain 1d10 + level HP as a bonus action once per short rest.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
    ],
)
