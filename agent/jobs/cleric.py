from agent.character.abilities import AbilityType, SkillType
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import CasterProgression
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import WeaponType
from agent.jobs.base import CharacterJob, JobOptions, JobSpecialization, JobType, ResourceDefinition
from agent.jobs.feature import EquipmentChoice, JobFeature, JobPassive, OptionItem, SubclassChoice
from agent.jobs.spell_loader import load_spell
from agent.models.enums import FeatureId

# https://roll20.net/compendium/dnd5e/Classes:Cleric#content


def channel_divinity_max_uses(level: int) -> int:
    """Calculate Channel Divinity max uses based on cleric level."""
    if level >= 18:  # noqa: PLR2004
        return 3
    if level >= 6:  # noqa: PLR2004
        return 2
    if level >= 2:  # noqa: PLR2004
        return 1
    return 0


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
        Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.MAGIC),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.ac_bonus_with_armor_types(
                source_id=JobType.CLERIC.value,
                name="Blessed Armor",
                description="+1 to AC while wearing light or medium armor.",
                value=1,
                armor_types=[ArmorType.LIGHT, ArmorType.MEDIUM],
            ),
            level_required=1,
        ),
    ],
    features=[],
    spells=[
        load_spell("sacred_flame.json"),
    ],
    resources=[
        ResourceDefinition(
            name="channel_divinity",
            calculate_max_uses=channel_divinity_max_uses,
            restore_on_short_rest=True,
            restore_on_long_rest=True,
        ),
    ],
)

LifeDomain = JobSpecialization(
    name="Life Domain",
    passives=[
        JobPassive(
            trait=TraitBuilder.healing_bonus(
                source_id=JobType.CLERIC.value,
                name="Disciple of Life",
                description=(
                    "Whenever you use a healing spell on a creature, the creature "
                    "regains additional hit points equal to 2 + the spell's level"
                ),
                value=2,
            ),
            level_required=1,
        ),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.PRESERVE_LIFE,
            name="Channel Divinity - Preserve Life",
            description=(
                "Once per combat, restore a number of hit points equal to five times your cleric level, "
                "divided among the target creatures."
            ),
            level_required=2,
            uses_per_rest=1,
        ),
    ],
    spells=[
        load_spell("cure_wounds.json"),
        load_spell("bless.json"),
        load_spell("lesser_restoration.json"),
        load_spell("spiritual_weapon.json"),
    ],
    proficiencies=[Proficiency(source="life_domain", type=ProficiencyType.ARMOR, target=ArmorType.HEAVY)],
)

WarDomain = JobSpecialization(
    name="War Domain",
    proficiencies=[
        Proficiency(source="war_domain", type=ProficiencyType.WEAPON, target=WeaponType.MARTIAL_MELEE),
        Proficiency(source="war_domain", type=ProficiencyType.ARMOR, target=ArmorType.HEAVY),
    ],
    passives=[
        JobPassive(
            trait=TraitBuilder.guided_strike(
                source_id=JobType.CLERIC.value,
                name="Guided Strike",
                description="Use Channel Divinity after seeing attack roll to gain +10 bonus.",
            ),
            level_required=2,
        ),
    ],
    features=[
        JobFeature(
            ref_id=FeatureId.WAR_PRIEST,
            name="War Priest",
            description="After the Attack action, make one weapon attack as a bonus action (WIS/rest, min 1).",
            level_required=1,
        ),
    ],
    spells=[
        load_spell("divine_favor.json"),
        load_spell("shield_of_faith.json"),
        load_spell("magic_weapon.json"),
        load_spell("spiritual_weapon.json"),
    ],
    resources=[
        ResourceDefinition(
            name="war_priest",
            calculate_max_uses=lambda _: 1,
            restore_on_short_rest=True,
            restore_on_long_rest=True,
        ),
    ],
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
