from agent.character.abilities import AbilityType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression, SpellLevel
from agent.effects.traits import TraitBuilder
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobFeature, JobType
from agent.jobs.feature import JobPassive
from agent.jobs.spells import AttackSpell
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType

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
        AttackSpell(
            ref_id=FeatureId.MAGIC_MISSILE,
            name="Magic Missile",
            description="Automatically hits and deals 1d4+1 force damage per missile.",
            level_required=1,
            is_aoe=False,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.MULTI,
            range=10,
            hits=3,
            damage_dice="1d4+1",
            damage_type=DamageType.FORCE,
            requires_save=False,
        ),
    ],
)
