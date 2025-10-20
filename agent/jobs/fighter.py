from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, FeatureType, JobFeature
from agent.models.constants import SECOND_WIND_ID

Fighter = CharacterJob(
    name="Fighter",
    hit_die=10,
    primary_stat=StatType.STR,
    save_proficiencies=[StatType.STR, StatType.CON],
    features=[
        JobFeature(
            name="Second Wind",
            description="Regain 1d10 + level HP as a bonus action once per short rest.",
            level_required=1,
            type=FeatureType.ACTIVE,
            reference_id=SECOND_WIND_ID,
            uses_per_rest=1,
        ),
    ],
)
