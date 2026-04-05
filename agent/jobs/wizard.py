from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.effects.traits import TraitBuilder
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobFeature, JobType
from agent.jobs.feature import JobPassive
from agent.jobs.spell_loader import load_spell
from agent.models.enums import FeatureId

# https://roll20.net/compendium/dnd5e/Classes:Wizard#content

Wizard = CharacterJob(
    type=JobType.WIZARD,
    hit_die=6,
    primary_ability=AbilityType.INT,
    spellcasting_ability=AbilityType.INT,
    spell_progression=CasterProgression.FULL,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.INT),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.WIS),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MAGIC),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.ac_bonus_without_armor(
                source_id=JobType.WIZARD.value,
                name="Mage Armor",
                description="+3 to AC while not wearing armor.",
                value=3,
            ),
            level_required=1,
        ),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.ARCANE_RECOVERY,
            name="Arcane Recovery",
            description="Once per combat, you can recover some expended spell slots.",
            level_required=1,
            uses_per_rest=1,
        )
    ],
    spells=[
        load_spell("magic_missile.json"),
    ],
)
