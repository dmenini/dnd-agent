from agent.character.stats import StatType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.enums import FeatureId

Rogue = CharacterJob(
    type=JobType.ROGUE,
    hit_die=8,
    primary_stat=StatType.DEX,
    save_proficiencies=[StatType.DEX, StatType.INT],
    weapon_proficiencies=[],
    features=[
        JobFeature(
            ref_id=FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE,
            name="Sneak Attack",
            description="Once per turn, deal +1d6 damage when attacking with advantage.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"dice_expr": "1d6"},
        ),
    ],
)
