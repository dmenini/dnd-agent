from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobFeature, JobType
from agent.jobs.feature import JobPassive
from agent.models.enums import FeatureId

# https://roll20.net/compendium/dnd5e/Classes:Fighter#content

Fighter = CharacterJob(
    type=JobType.FIGHTER,
    hit_die=10,
    primary_ability=AbilityType.STR,
    spell_progression=CasterProgression.NONE,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.STR),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.CON),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.LIGHT),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.MEDIUM),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.HEAVY),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.SHIELD),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_RANGED),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.ac_bonus_with_armor(
                source_id=JobType.FIGHTER.value,
                name="Fighting Style - Defense",
                value=1,
            ),
            level_required=1,
        )
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.SECOND_WIND,
            name="Second Wind",
            description="Regain 1d10 + level HP as a bonus action once per combat.",
            level_required=1,
            uses_per_rest=1,
        ),
    ],
)
