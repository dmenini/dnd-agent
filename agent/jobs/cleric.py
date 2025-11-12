from agent.character.abilities import AbilityType, SkillType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression, SpellLevel
from agent.effects.status_effects.blessed import Blessed
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobOptions, JobType
from agent.jobs.feature import EquipmentChoice, FeatureChoice, FeatureType, JobFeature
from agent.jobs.spells import AttackSpell, HealingSpell, SupportSpell
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType

# https://roll20.net/compendium/dnd5e/Classes:Cleric#content

ClericOptions = JobOptions(
    job_type=JobType.CLERIC,
    skill_choices=[
        SkillType.HISTORY,
        SkillType.INSIGHT,
        SkillType.MEDICINE,
        SkillType.PERSUASION,
        SkillType.RELIGION,
    ],
    skill_count=2,
    equipment_choices=[
        EquipmentChoice(
            slot=EquipmentSlot.MAIN_HAND,
            options=["Mace", "Warhammer (if proficient)"],
            description="Choose your primary weapon",
        ),
        EquipmentChoice(
            slot=EquipmentSlot.ARMOR,
            options=["Scale Mail", "Leather Armor", "Chain Mail (if proficient)"],
            description="Choose your armor",
        ),
        EquipmentChoice(
            slot=EquipmentSlot.RANGED,
            options=["Light Crossbow and 20 bolts", "Any simple weapon"],
            description="Choose your secondary weapon",
        ),
    ],
    feature_choices=[
        FeatureChoice(
            feature_name="Divine Domain",
            options=[
                "Life Domain - Focus on healing and vitality",
                "War Domain - Divine warrior with combat prowess",
                "Tempest Domain - Channel the power of storms",
                "Knowledge Domain - Keeper of lore and secrets",
                "Trickery Domain - Master of deception and stealth",
                "Nature Domain - Protector of the wilderness",
                "Light Domain - Bearer of radiant flame",
            ],
            description="Your divine domain represents the aspect of your deity's portfolio you embody",
            level_required=1,
        ),
    ],
)

Cleric = CharacterJob(
    type=JobType.CLERIC,
    hit_die=8,
    primary_ability=AbilityType.WIS,
    spellcasting_ability=AbilityType.WIS,
    spell_progression=CasterProgression.FULL,
    proficiencies=[
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.WIS),
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.CHA),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.LIGHT),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.MEDIUM),
        Proficiency(type=ProficiencyType.ARMOR, target=ArmorType.SHIELD),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE),
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_RANGED),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.SPELL_SAVE_ADVANTAGE,
            name="Spellcasting",
            description="Gain ability to cast spells using WIS.",
            level_required=1,
            type=FeatureType.PASSIVE,
        ),
        JobFeature(
            ref_id=FeatureId.DIVINE_RESTORATION,
            name="Channel Divinity - Restore Vitality",
            description="Once per combat, channel divine power to heal allies.",
            level_required=1,
            type=FeatureType.ACTIVE,
            uses_per_rest=1,
        ),
        JobFeature(
            ref_id=FeatureId.AC_BONUS_WITH_ARMOR_TYPES,
            name="Blessed Armor",
            description="+1 to AC while wearing light or medium armor.",
            level_required=1,
            type=FeatureType.PASSIVE,
            kwargs={"value": 1, "armor_types": [ArmorType.LIGHT, ArmorType.MEDIUM]},
        ),
    ],
    spells=[
        AttackSpell(
            ref_id=FeatureId.SACRED_FLAME,
            name="Sacred Flame",
            description="Call down radiant fire to deal 1d8 radiant damage. Target makes a DEX save for no damage.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.SINGLE,
            range=12,
            damage_dice="1d8",
            damage_type=DamageType.RADIANT,
            requires_save=True,
            ability=AbilityType.DEX,
        ),
        HealingSpell(
            ref_id=FeatureId.CURE_WOUNDS,
            name="Cure Wounds",
            description="Touch a creature to restore 1d8 + WIS modifier hit points.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.SINGLE,
            range=1,
            heal_dice="1d8",
        ),
        SupportSpell(
            ref_id=FeatureId.BLESS,
            name="Bless",
            description="Up to three allies gain +1d4 to attack rolls and saving throws.",
            level_required=1,
            type=FeatureType.ACTIVE,
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.MULTI,
            range=9,
            hits=3,
            effects=[Blessed(duration=1)],
        ),
    ],
)
