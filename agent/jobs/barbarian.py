from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.enums import FeatureId

Barbarian = CharacterJob(
    type=JobType.BARBARIAN,
    hit_die=12,
    primary_ability=AbilityType.STR,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.CON),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.STR),
    ],
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
            ref_id=FeatureId.AC_BONUS_MOD_WITHOUT_ARMOR,
            name="Unarmored Defense",
            description="While not wearing armor, AC = 10 + DEX + CON modifier.",
            level_required=1,
            type=FeatureType.PASSIVE,
        ),
    ],
)
