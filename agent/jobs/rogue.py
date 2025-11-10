from agent.character.abilities import AbilityType, SkillType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.enums import FeatureId

Rogue = CharacterJob(
    type=JobType.ROGUE,
    hit_die=8,
    primary_ability=AbilityType.DEX,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.DEX),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.INT),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE,
            name="Sneak Attack",
            description="Once per turn, deal +1d6 damage when attacking with advantage.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"dice_expr": "1d6"},
        ),
        JobFeature(
            ref_id=FeatureId.EXPERTISE,
            name="Stealth Expertise",
            description="Double proficiency bonus for stealth skill checks.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"proficiency": SkillType.STEALTH},
        ),
        JobFeature(
            ref_id=FeatureId.EXPERTISE,
            name="Perception Expertise",
            description="Double proficiency bonus for perception skill checks.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"proficiency": SkillType.PERCEPTION},
        ),
    ],
)
