import pytest

from agent.character.character import Character
from agent.character.resolvers.equipment import EquipmentResolver
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.equipment.armor import Amulet, Armor, ArmorType, Ring, Shield
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling, WeaponType
from agent.jobs.fighter import Fighter
from agent.models.damage import DamageType


@pytest.fixture
def equipment_resolver() -> EquipmentResolver:
    return EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())


dagger = MeleeWeapon(
    name="Dagger",
    weapon_type=WeaponType.SIMPLE_MELEE,
    handling=WeaponHandling.ONE_HANDED,
    stat=StatType.DEX,
    damage_dice="1d4",
    damage_type=DamageType.PIERCING,
    finesse=True,
    dual_wield=True,
)

longsword = MeleeWeapon(
    name="Longsword",
    weapon_type=WeaponType.MARTIAL_MELEE,
    handling=WeaponHandling.VERSATILE,
    stat=StatType.STR,
    damage_dice="1d8",
    versatile_damage="1d10",
    damage_type=DamageType.SLASHING,
)

greatsword = MeleeWeapon(
    name="Greatsword",
    weapon_type=WeaponType.MARTIAL_MELEE,
    handling=WeaponHandling.TWO_HANDED,
    stat=StatType.STR,
    damage_dice="2d6",
    damage_type=DamageType.SLASHING,
)

bow = RangedWeapon(
    name="Bow", weapon_type=WeaponType.SIMPLE_RANGE, damage_type=DamageType.PIERCING, damage_dice="1d20",
    handling=WeaponHandling.ONE_HANDED,
)


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
    assert actor.shield is shield

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
    actor.unequip("armor")
    assert actor.armor is None


def test_state_change_recomputes_traits(actor: Character) -> None:
    actor.unequip("armor")
    actor.change_job(Fighter)

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 0

    actor.armor = Armor(name="armor", armor_type=ArmorType.MEDIUM, base_ac=5)
    actor.equip_all()

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 1


def test_equip_one_handed(actor) -> None:
    actor.equip_melee_weapon(dagger, "main_hand")
    assert actor.main_hand == dagger
    assert actor.off_hand is None
    assert not actor._two_handed_active


def test_equip_two_handed(actor) -> None:
    actor.equip_melee_weapon(greatsword, "main_hand")
    assert actor.main_hand == greatsword
    assert actor.off_hand is None
    assert actor._two_handed_active


def test_equip_versatile_two_hands_if_free(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(longsword, "main_hand")
    # off-hand free → should use two hands
    assert actor.main_hand == longsword
    assert actor.off_hand is None
    assert actor._two_handed_active


def test_equip_versatile_one_hand_if_offhand_occupied(actor: EquipmentResolver) -> None:
    actor.off_hand = dagger
    actor.equip_melee_weapon(longsword, "main_hand")
    # off-hand occupied → one hand only
    assert actor.main_hand == longsword
    assert actor.off_hand == dagger
    assert not actor._two_handed_active


def test_replace_weapon(actor: EquipmentResolver) -> None:
    actor.equip_melee_weapon(dagger, "main_hand")
    actor.equip_melee_weapon(longsword, "main_hand")
    # dagger should be unequipped
    assert actor.main_hand == longsword
    assert actor._two_handed_active
