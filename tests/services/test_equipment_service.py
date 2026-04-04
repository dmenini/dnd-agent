"""Tests for EquipmentService."""

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType, Shield
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling, WeaponType
from agent.models.damage import DamageType
from agent.services.equipment_service import EquipmentService


def test_equip_armor(fighter: Character) -> None:
    """Test equipping armor."""
    armor = Armor(
        name="Plate Armor",
        description="Heavy armor",
        armor_type=ArmorType.HEAVY,
        base_ac=18,
    )

    EquipmentService.equip(fighter, armor, EquipmentSlot.ARMOR)

    assert fighter.equipment.armor == armor
    assert fighter.equipment.armor.name == "Plate Armor"


def test_equip_shield(fighter: Character) -> None:
    """Test equipping a shield."""
    shield = Shield(
        name="Steel Shield",
        description="A sturdy shield",
        ac_bonus=2,
    )

    EquipmentService.equip(fighter, shield, EquipmentSlot.OFF_HAND)

    assert fighter.equipment.off_hand == shield
    assert isinstance(fighter.equipment.off_hand, Shield)


def test_equip_weapon_main_hand(fighter: Character) -> None:
    """Test equipping a weapon in main hand."""
    sword = MeleeWeapon(
        name="Longsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.VERSATILE,
        ability=AbilityType.STR,
        damage_dice="1d8",
        versatile_damage="1d10",
        damage_type=DamageType.SLASHING,
    )

    EquipmentService.equip(fighter, sword, EquipmentSlot.MAIN_HAND)

    assert fighter.equipment.main_hand == sword


def test_equip_two_handed_weapon(fighter: Character) -> None:
    """Test equipping a two-handed weapon clears off-hand."""
    # First equip something in off-hand
    dagger = MeleeWeapon(
        name="Dagger",
        weapon_type=WeaponType.SIMPLE_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.DEX,
        damage_dice="1d4",
        damage_type=DamageType.PIERCING,
        dual_wield=True,
    )
    EquipmentService.equip(fighter, dagger, EquipmentSlot.OFF_HAND)
    assert fighter.equipment.off_hand is not None

    # Now equip two-handed weapon
    greatsword = MeleeWeapon(
        name="Greatsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.TWO_HANDED,
        ability=AbilityType.STR,
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
    )

    EquipmentService.equip(fighter, greatsword, EquipmentSlot.MAIN_HAND)

    assert fighter.equipment.main_hand == greatsword
    assert fighter.equipment.off_hand is None
    assert fighter.equipment.two_handed_active is True


def test_equip_versatile_weapon(fighter: Character) -> None:
    """Test equipping a versatile weapon."""
    longsword = MeleeWeapon(
        name="Longsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.VERSATILE,
        ability=AbilityType.STR,
        damage_dice="1d8",
        versatile_damage="1d10",
        damage_type=DamageType.SLASHING,
    )

    # Equip with empty off-hand -> should use two hands
    EquipmentService.equip(fighter, longsword, EquipmentSlot.MAIN_HAND)

    assert fighter.equipment.main_hand == longsword
    assert fighter.equipment.two_handed_active is True


def test_equip_ranged_weapon(fighter: Character) -> None:
    """Test equipping a ranged weapon."""
    bow = RangedWeapon(
        name="Longbow",
        weapon_type=WeaponType.MARTIAL_RANGED,
        damage_dice="1d8",
        damage_type=DamageType.PIERCING,
        handling=WeaponHandling.TWO_HANDED,
    )

    EquipmentService.equip(fighter, bow, EquipmentSlot.RANGED)

    assert fighter.equipment.ranged == bow


def test_unequip(fighter: Character) -> None:
    """Test unequipping an item."""
    sword = MeleeWeapon(
        name="Shortsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.STR,
        damage_dice="1d6",
        damage_type=DamageType.SLASHING,
    )

    EquipmentService.equip(fighter, sword, EquipmentSlot.MAIN_HAND)
    assert fighter.equipment.main_hand is not None

    EquipmentService.unequip(fighter, EquipmentSlot.MAIN_HAND)

    assert fighter.equipment.main_hand is None


def test_equip_replaces_existing(fighter: Character) -> None:
    """Test that equipping in occupied slot replaces existing item."""
    sword1 = MeleeWeapon(
        name="Sword 1",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.STR,
        damage_dice="1d6",
        damage_type=DamageType.SLASHING,
    )
    sword2 = MeleeWeapon(
        name="Sword 2",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.STR,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
    )

    EquipmentService.equip(fighter, sword1, EquipmentSlot.MAIN_HAND)
    assert fighter.equipment.main_hand is not None
    assert fighter.equipment.main_hand.name == "Sword 1"

    EquipmentService.equip(fighter, sword2, EquipmentSlot.MAIN_HAND)
    assert fighter.equipment.main_hand is not None
    assert fighter.equipment.main_hand.name == "Sword 2"


def test_equip_all(fighter: Character) -> None:
    """Test equip_all re-equips all slotted items."""
    # Fighter fixture already has equipment equipped
    initial_main_hand = fighter.equipment.main_hand

    # equip_all should call on_equip for all items
    EquipmentService.equip_all(fighter)

    # Items should still be equipped
    assert fighter.equipment.main_hand == initial_main_hand


def test_resolve_slot_for_armor(fighter: Character) -> None:
    """Test automatic slot resolution for armor."""
    armor = Armor(
        name="Chainmail",
        description="Medium armor",
        armor_type=ArmorType.MEDIUM,
        base_ac=16,
    )

    # Equip without specifying slot
    EquipmentService.equip(fighter, armor)

    assert fighter.equipment.armor == armor


def test_resolve_slot_for_weapon(fighter: Character) -> None:
    """Test automatic slot resolution for weapons."""
    # Unequip current weapon
    EquipmentService.unequip(fighter, EquipmentSlot.MAIN_HAND)

    sword = MeleeWeapon(
        name="Sword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.STR,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
    )

    # Equip without specifying slot -> should go to main hand
    EquipmentService.equip(fighter, sword)

    assert fighter.equipment.main_hand == sword
