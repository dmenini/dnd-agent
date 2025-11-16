from agent.character.abilities import AbilityType, SkillType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.feature import JobPassive

# https://roll20.net/compendium/dnd5e/Classes:Rogue#content

Rogue = CharacterJob(
    type=JobType.ROGUE,
    hit_die=8,
    primary_ability=AbilityType.DEX,
    spell_progression=CasterProgression.NONE,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.DEX),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.INT),
        Proficiency(type=ProficiencyType.SKILL, target=SkillType.STEALTH),
        Proficiency(type=ProficiencyType.SKILL, target=SkillType.PERCEPTION),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.LIGHT),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_RANGED),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.sneak_attack(
                source_id=JobType.ROGUE.value,
                name="Sneak Attack",
                description="Once per turn, deal +1d6 damage when attacking with advantage.",
                dice_expr="1d6",
            ),
            level_required=1,
        ),
        JobPassive(
            trait=TraitBuilder.expertise(  # TODO: Should be chosen by player
                source_id=JobType.ROGUE.value,
                name="Stealth Expertise",
                description="Double proficiency bonus for stealth skill checks.",
                proficiency=SkillType.STEALTH,
            ),
            level_required=1,
        ),
        JobPassive(
            trait=TraitBuilder.expertise(  # TODO: Should be chosen by player
                source_id=JobType.ROGUE.value,
                name="Perception Expertise",
                description="Double proficiency bonus for perception skill checks.",
                proficiency=SkillType.PERCEPTION,
            ),
            level_required=1,
        ),
    ],
)
