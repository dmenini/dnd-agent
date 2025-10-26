from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import FeatureType
from agent.models.enums import FeatureId

Fighter = CharacterJob(
    name="Fighter",
    hit_die=10,
    primary_stat=StatType.STR,
    save_proficiencies=[StatType.STR, StatType.CON],
    weapon_proficiencies=[],
    features=[
        JobFeature(
            ref_id=FeatureId.AC_BONUS_WITH_ARMOR,
            name="Fighting Style: Defense",
            description="+1 to AC while wearing armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"value": 1},
        ),
        JobFeature(
            ref_id=FeatureId.SECOND_WIND,
            name="Second Wind",
            description="Regain 1d10 + level HP as a bonus action once per combat.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
    ],
)
