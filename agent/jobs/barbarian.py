from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import JobFeature, JobPassive
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
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_RANGED),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.ac_mod_bonus_without_armor(
                source_id=JobType.BARBARIAN.value,
                name="Mage Armor",
                description="+3 to AC while not wearing armor.",
                ability=AbilityType.CON,
            ),
            level_required=1,
        ),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.RAGE,
            name="Rage",
            description="Enter a rage as a bonus action to gain advantage on STR checks and bonus melee damage.",
            level_required=1,
            uses_per_rest=2,
            kwargs={"damage_bonus": 2},
        ),
    ],
)
