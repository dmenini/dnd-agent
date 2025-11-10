from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobFeature, JobType
from agent.jobs.feature import FeatureType
from agent.models.enums import FeatureId

Fighter = CharacterJob(
    type=JobType.FIGHTER,
    hit_die=10,
    primary_ability=AbilityType.STR,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.STR),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.CON),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.LIGHT),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.MEDIUM),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.HEAVY),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_RANGED),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.AC_BONUS_WITH_ARMOR,
            name="Fighting Style - Defense",
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
