from agent.character.abilities import AbilityType, SkillType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression, SpellLevel
from agent.effects.status_effects.collection import Blessed
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobOptions, JobSpecialization, JobType
from agent.jobs.feature import EquipmentChoice, JobFeature, JobPassive, OptionItem, SubclassChoice
from agent.jobs.spells import AttackSpell, HealingSpell, SupportSpell
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType

# https://roll20.net/compendium/dnd5e/Classes:Cleric#content


ClericOptions = JobOptions(
    job_type=JobType.CLERIC,
    skill_options=[
        SkillType.HISTORY,
        SkillType.INSIGHT,
        SkillType.MEDICINE,
        SkillType.PERSUASION,
        SkillType.RELIGION,
    ],
    skill_count=2,
    equipment_options=[
        EquipmentChoice(
            slot=EquipmentSlot.MAIN_HAND,
            options=[
                OptionItem(id="mace", name="Mace", description=""),
                OptionItem(id="warhammer", name="Warhammer", description="Requires martial proficiency"),
            ],
            description="Choose your main weapon",
        ),
        EquipmentChoice(
            slot=EquipmentSlot.ARMOR,
            options=[
                OptionItem(id="scale_mail", name="Scale Mail"),
                OptionItem(id="leather_armor", name="Leather Armor"),
                OptionItem(id="chain_mail", name="Chain Mail", description="Requires heavy armor proficiency"),
            ],
            description="Choose your armor",
        ),
        EquipmentChoice(
            slot=EquipmentSlot.RANGED,
            options=[
                OptionItem(id="light_crossbow", name="Light Crossbow"),
                OptionItem(id="light_bow", name="Light Bow"),
            ],
            description="Choose your ranged weapon",
        ),
    ],
    subclass_options=SubclassChoice(
        feature_name="Divine Domain",
        description="Your divine domain represents the aspect of your deity's portfolio you embody.",
        options=[
            OptionItem(id="life_domain", name="Life Domain", description="Focus on healing and vitality"),
            OptionItem(id="war_domain", name="War Domain", description="Divine warrior with combat prowess"),
            OptionItem(id="tempest_domain", name="Tempest Domain", description="Channel the power of storms"),
            OptionItem(id="knowledge_domain", name="Knowledge Domain", description="Keeper of lore and secrets"),
            OptionItem(id="trickery_domain", name="Trickery Domain", description="Master of deception and stealth"),
            OptionItem(id="nature_domain", name="Nature Domain", description="Protector of the wilderness"),
            OptionItem(id="light_domain", name="Light Domain", description="Bearer of radiant flame"),
        ],
        level_required=1,
    ),
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
    passives=[
        JobPassive(
            trait=TraitBuilder.ac_bonus_with_armor_types(
                source_id=JobType.BARBARIAN.value,
                name="Blessed Armor",
                description="+1 to AC while wearing light or medium armor.",
                value=1,
                armor_types=[ArmorType.LIGHT, ArmorType.MEDIUM],
            ),
            level_required=1,
        ),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.DIVINE_RESTORATION,
            name="Channel Divinity - Restore Vitality",
            description="Once per combat, channel divine power to heal allies.",
            level_required=1,
            uses_per_rest=1,
        ),
    ],
    spells=[
        AttackSpell(
            ref_id=FeatureId.SACRED_FLAME,
            name="Sacred Flame",
            description="Call down radiant fire to deal 1d8 radiant damage. Target makes a DEX save for no damage.",
            level_required=1,
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
            level=SpellLevel.LEVEL_1,
            targeting=TargetingType.ALLIES,
            range=9,
            hits=3,
            effects=[Blessed.with_duration(1)],
        ),
    ],
)

LifeDomain = JobSpecialization(
    name="Life Domain",
)

WarDomain = JobSpecialization(
    name="War Domain",
    proficiencies=[Proficiency(source="war_domain", type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE)],
)

TempestDomain = JobSpecialization(
    name="Tempest Domain",
    proficiencies=[Proficiency(source="tempest_domain", type=ProficiencyType.ARMOR, target=ArmorType.HEAVY)],
)

KnowledgeDomain = JobSpecialization(
    name="Knowledge Domain",
)

TrickeryDomain = JobSpecialization(
    name="Trickery Domain",
)

NatureDomain = JobSpecialization(
    name="Nature Domain",
)

LightDomain = JobSpecialization(
    name="Light Domain",
)

cleric_specs = {
    "life_domain": LifeDomain,
    "war_domain": WarDomain,
    "tempest_domain": TempestDomain,
    "knowledge_domain": KnowledgeDomain,
    "trickery_domain": TrickeryDomain,
    "nature_domain": NatureDomain,
    "light_domain": LightDomain,
}
