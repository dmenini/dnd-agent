import pytest

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.character.resolvers.equipment import EquipmentResolver
from agent.character.resources import ActionEconomy
from agent.equipment.armor import Amulet, Armor, ArmorType, Ring, Shield
from agent.equipment.base import EquipmentSlot, EquipmentType
from agent.equipment.inventory import Inventory
from agent.equipment.weapons import MeleeWeapon, Weapon, WeaponHandling, WeaponType
from agent.jobs.fighter import Fighter
from agent.models.damage import DamageType
from tests.conftest import bow, dagger, greatsword, longsword


@pytest.fixture
def equipment_resolver() -> EquipmentResolver:
    return EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())


def test_equip_weapon_assigns_to_main_hand(actor: EquipmentResolver) -> None:
    actor.equip(dagger)
    assert actor.main_hand is dagger


def test_second_weapon_goes_to_off_hand(actor: EquipmentResolver) -> None:
    actor.main_hand = dagger
    actor.equip(dagger)
    assert actor.off_hand is dagger


def test_ranged_weapon_goes_to_ranged(actor: EquipmentResolver) -> None:
    actor.main_hand = dagger
    actor.off_hand = dagger
    actor.equip(bow)
    assert actor.ranged is bow


def test_armor_and_shield_slots(actor: EquipmentResolver) -> None:
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    shield = Shield(name="Shield")

    actor.equip(armor)
    actor.equip(shield)

    assert actor.armor is armor
    assert actor.off_hand is shield

    assert actor.armor_class == 13


def test_amulet_and_rings_auto_assign(actor: EquipmentResolver) -> None:
    amulet = Amulet(name="Amulet of Health")
    ring1 = Ring(name="Ring of Protection")
    ring2 = Ring(name="Ring of Regeneration")

    actor.equip(amulet)
    actor.equip(ring1)
    actor.equip(ring2)

    assert actor.amulet is amulet
    assert actor.ring_left is ring1
    assert actor.ring_right is ring2

    # Another ring replaces left
    ring3 = Ring(name="Ring of Speed")
    actor.equip(ring3)
    assert actor.ring_left is ring3

    # Another ring replaces right
    actor.equip(ring1)
    assert actor.ring_right is ring1


def test_unequip_clears_slot_and_calls_on_unequip(actor: EquipmentResolver) -> None:
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    actor.equip(armor)
    actor.unequip(EquipmentSlot.ARMOR)
    assert actor.armor is None


def test_state_change_recomputes_traits(actor: Character) -> None:
    actor.unequip(EquipmentSlot.ARMOR)
    actor.change_job(Fighter)

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 0

    actor.armor = Armor(name="armor", armor_type=ArmorType.MEDIUM, base_ac=5)
    actor.equip_all()

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 1


def test_equip_one_handed(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(dagger, EquipmentSlot.MAIN_HAND)
    assert actor.main_hand == dagger
    assert actor.off_hand is None
    assert not actor.two_handed_active


def test_equip_two_handed(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(greatsword, EquipmentSlot.MAIN_HAND)
    assert actor.main_hand == greatsword
    assert actor.off_hand is None
    assert actor.two_handed_active


def test_equip_versatile_two_hands_if_free(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(longsword, EquipmentSlot.MAIN_HAND)
    # off-hand free → should use two hands
    assert actor.main_hand == longsword
    assert actor.off_hand is None
    assert actor.two_handed_active


def test_equip_versatile_one_hand_if_offhand_occupied(actor: EquipmentResolver) -> None:
    actor.off_hand = dagger
    actor.equip_melee_weapon(longsword, EquipmentSlot.MAIN_HAND)
    # off-hand occupied → one hand only
    assert actor.main_hand == longsword
    assert actor.off_hand == dagger
    assert not actor.two_handed_active


def test_replace_weapon(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(dagger, EquipmentSlot.MAIN_HAND)
    actor.equip_melee_weapon(longsword, EquipmentSlot.MAIN_HAND)
    # dagger should be unequipped
    assert actor.main_hand == longsword
    assert actor.two_handed_active


def test_dual_wield_one_handed(actor: EquipmentResolver) -> None:
    # Equip dagger in main hand
    actor.equip_melee_weapon(dagger, EquipmentSlot.MAIN_HAND)
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
    actor.equip_melee_weapon(off_dagger, EquipmentSlot.OFF_HAND)

    assert actor.main_hand == dagger
    assert actor.off_hand == off_dagger
    assert not actor.two_handed_active


def test_two_handed_weapon_replaces_existing_main_and_off_hand(actor: EquipmentResolver) -> None:
    # Equip dual-wield setup first
    actor.equip_melee_weapon(dagger, EquipmentSlot.MAIN_HAND)
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
    actor.equip_melee_weapon(off_dagger, EquipmentSlot.OFF_HAND)

    # Equip two-handed weapon
    actor.equip_melee_weapon(greatsword, EquipmentSlot.MAIN_HAND)
    assert actor.main_hand == greatsword
    assert actor.off_hand is None
    assert actor.two_handed_active


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
