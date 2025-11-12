from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import FeatureType, JobFeature
from agent.models.enums import FeatureId

# https://roll20.net/compendium/dnd5e/Classes:Barbarian#content

Barbarian = CharacterJob(
    type=JobType.BARBARIAN,
    hit_die=12,
    primary_ability=AbilityType.STR,
    spell_progression=CasterProgression.NONE,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.CON),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.STR),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.LIGHT),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.MEDIUM),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.SHIELD),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE),
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
