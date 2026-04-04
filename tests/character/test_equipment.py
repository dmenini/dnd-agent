from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.equipment.armor import Amulet, Armor, ArmorType, Ring, Shield
from agent.equipment.base import EquipmentSlot, EquipmentType
from agent.equipment.inventory import Inventory
from agent.equipment.weapons import MeleeWeapon, Weapon, WeaponHandling, WeaponType
from agent.jobs.fighter import Fighter
from agent.models.damage import DamageType
from agent.services.equipment_service import EquipmentService
from agent.services.job_service import JobService
from tests.conftest import bow, dagger, greatsword, longsword


def test_equip_weapon_assigns_to_main_hand(actor: Character) -> None:
    EquipmentService.equip(actor, dagger)
    assert actor.equipment.main_hand is dagger


def test_second_weapon_goes_to_off_hand(actor: Character) -> None:
    actor.equipment.main_hand = dagger
    EquipmentService.equip(actor, dagger)
    assert actor.equipment.off_hand is dagger


def test_ranged_weapon_goes_to_ranged(actor: Character) -> None:
    actor.equipment.main_hand = dagger
    actor.equipment.off_hand = dagger
    EquipmentService.equip(actor, bow)
    assert actor.equipment.ranged is bow


def test_armor_and_shield_slots(actor: Character) -> None:
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    shield = Shield(name="Shield")

    EquipmentService.equip(actor, armor)
    EquipmentService.equip(actor, shield)

    assert actor.equipment.armor is armor
    assert actor.equipment.off_hand is shield

    assert actor.armor_class == 13


def test_amulet_and_rings_auto_assign(actor: Character) -> None:
    amulet = Amulet(name="Amulet of Health")
    ring1 = Ring(name="Ring of Protection")
    ring2 = Ring(name="Ring of Regeneration")

    EquipmentService.equip(actor, amulet)
    EquipmentService.equip(actor, ring1)
    EquipmentService.equip(actor, ring2)

    assert actor.equipment.amulet is amulet
    assert actor.equipment.ring_left is ring1
    assert actor.equipment.ring_right is ring2

    # Another ring replaces left
    ring3 = Ring(name="Ring of Speed")
    EquipmentService.equip(actor, ring3)
    assert actor.equipment.ring_left is ring3

    # Another ring replaces right
    EquipmentService.equip(actor, ring1)
    assert actor.equipment.ring_right is ring1


def test_unequip_clears_slot_and_calls_on_unequip(actor: Character) -> None:
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    EquipmentService.equip(actor, armor)
    EquipmentService.unequip(actor, EquipmentSlot.ARMOR)
    assert actor.equipment.armor is None


def test_state_change_recomputes_traits(actor: Character) -> None:
    EquipmentService.unequip(actor, EquipmentSlot.ARMOR)
    JobService.change_job(actor, Fighter)

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 0

    actor.equipment.armor = Armor(name="armor", armor_type=ArmorType.MEDIUM, base_ac=5)
    EquipmentService.equip_all(actor)

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 1


def test_equip_one_handed(actor: Character) -> None:
    EquipmentService.equip_melee_weapon(actor, dagger, EquipmentSlot.MAIN_HAND)
    assert actor.equipment.main_hand == dagger
    assert actor.equipment.off_hand is None
    assert not actor.equipment.two_handed_active


def test_equip_two_handed(actor: Character) -> None:
    EquipmentService.equip_melee_weapon(actor, greatsword, EquipmentSlot.MAIN_HAND)
    assert actor.equipment.main_hand == greatsword
    assert actor.equipment.off_hand is None
    assert actor.equipment.two_handed_active


def test_equip_versatile_two_hands_if_free(actor: Character) -> None:
    EquipmentService.equip_melee_weapon(actor, longsword, EquipmentSlot.MAIN_HAND)
    # off-hand free → should use two hands
    assert actor.equipment.main_hand == longsword
    assert actor.equipment.off_hand is None
    assert actor.equipment.two_handed_active


def test_equip_versatile_one_hand_if_offhand_occupied(actor: Character) -> None:
    actor.equipment.off_hand = dagger
    EquipmentService.equip_melee_weapon(actor, longsword, EquipmentSlot.MAIN_HAND)
    # off-hand occupied → one hand only
    assert actor.equipment.main_hand == longsword
    assert actor.equipment.off_hand == dagger
    assert not actor.equipment.two_handed_active


def test_replace_weapon(actor: Character) -> None:
    EquipmentService.equip_melee_weapon(actor, dagger, EquipmentSlot.MAIN_HAND)
    EquipmentService.equip_melee_weapon(actor, longsword, EquipmentSlot.MAIN_HAND)
    # dagger should be unequipped
    assert actor.equipment.main_hand == longsword
    assert actor.equipment.two_handed_active


def test_dual_wield_one_handed(actor: Character) -> None:
    # Equip dagger in main hand
    EquipmentService.equip_melee_weapon(actor, dagger, EquipmentSlot.MAIN_HAND)
    # Equip another light weapon in off-hand
    off_dagger = MeleeWeapon(
        name="Other dagger",
        weapon_type=WeaponType.SIMPLE_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.DEX,
        damage_dice="1d4",
        damage_type=DamageType.PIERCING,
        finesse=True,
        dual_wield=True,
    )
    EquipmentService.equip_melee_weapon(actor, off_dagger, EquipmentSlot.OFF_HAND)

    assert actor.equipment.main_hand == dagger
    assert actor.equipment.off_hand == off_dagger
    assert not actor.equipment.two_handed_active


def test_two_handed_weapon_replaces_existing_main_and_off_hand(actor: Character) -> None:
    # Equip dual-wield setup first
    EquipmentService.equip_melee_weapon(actor, dagger, EquipmentSlot.MAIN_HAND)
    off_dagger = MeleeWeapon(
        name="Pippo",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.DEX,
        damage_dice="1d4",
        damage_type=DamageType.PIERCING,
        finesse=True,
        dual_wield=True,
    )
    EquipmentService.equip_melee_weapon(actor, off_dagger, EquipmentSlot.OFF_HAND)

    # Equip two-handed weapon
    EquipmentService.equip_melee_weapon(actor, greatsword, EquipmentSlot.MAIN_HAND)
    assert actor.equipment.main_hand == greatsword
    assert actor.equipment.off_hand is None
    assert actor.equipment.two_handed_active


def test_equipment_deserialization() -> None:
    inventory_json = {
        "equipment": [
            {
                "type": "weapon_melee",
                "name": "Longsword",
                "weapon_type": "martial_melee",
                "ability": "strength",
                "damage_dice": "1d8",
                "damage_type": "slashing",
            },
            {"type": "armor", "name": "Chain Shirt", "base_ac": 13, "armor_type": "light"},
            {"type": "shield", "name": "Steel Shield", "ac_bonus": 2},
        ]
    }

    inventory = Inventory.model_validate(inventory_json)

    weapon = inventory.equipment[0]
    assert isinstance(weapon, Weapon)
    assert isinstance(weapon, MeleeWeapon)
    assert weapon.type == EquipmentType.WEAPON_MELEE
    assert weapon.damage_dice == "1d8"

    armor = inventory.equipment[1]
    assert isinstance(armor, Armor)
    assert armor.type == EquipmentType.ARMOR
    assert armor.base_ac == 13

    shield = inventory.equipment[2]
    assert isinstance(shield, Shield)
    assert shield.type == EquipmentType.SHIELD
    assert shield.ac_bonus == 2
