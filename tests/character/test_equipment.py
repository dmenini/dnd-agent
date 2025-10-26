from agent.character.character import Character
from agent.character.resolvers.equipment import EquipmentResolver
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.equipment.armor import Amulet, Armor, ArmorType, Ring, Shield
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponType
from agent.jobs.fighter import Fighter
from agent.models.damage import DamageType


def get_weapon(name: str) -> MeleeWeapon:
    return MeleeWeapon(
        name=name,
        weapon_type=WeaponType.SIMPLE_MELEE,
        stat=StatType.STR,
        damage_type=DamageType.SLASHING,
        damage_dice="1d20",
    )


def test_equip_weapon_assigns_to_main_hand() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    sword = get_weapon(name="Sword")
    hero.equip(sword)
    assert hero.main_hand is sword


def test_second_weapon_goes_to_off_hand() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    sword = get_weapon(name="Shortsword")
    hero.main_hand = sword
    dagger = get_weapon(name="Dagger")
    hero.equip(dagger)
    assert hero.off_hand is dagger


def test_third_weapon_goes_to_ranged() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    hero.main_hand = get_weapon(name="Shortsword")
    hero.off_hand = get_weapon(name="Dagger")
    bow = RangedWeapon(
        name="Bow", weapon_type=WeaponType.SIMPLE_RANGE, damage_type=DamageType.PIERCING, damage_dice="1d20"
    )
    hero.equip(bow)
    assert hero.ranged is bow


def test_armor_and_shield_slots() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    shield = Shield(name="Shield")

    hero.equip(armor)
    hero.equip(shield)

    assert hero.armor is armor
    assert hero.shield is shield


def test_amulet_and_rings_auto_assign() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    amulet = Amulet(name="Amulet of Health")
    ring1 = Ring(name="Ring of Protection")
    ring2 = Ring(name="Ring of Regeneration")

    hero.equip(amulet)
    hero.equip(ring1)
    hero.equip(ring2)

    assert hero.amulet is amulet
    assert hero.ring_left is ring1
    assert hero.ring_right is ring2

    # Another ring replaces left
    ring3 = Ring(name="Ring of Speed")
    hero.equip(ring3)
    assert hero.ring_left is ring3

    # Another ring replaces right
    hero.equip(ring1)
    assert hero.ring_right is ring1


def test_unequip_clears_slot_and_calls_on_unequip() -> None:
    hero = EquipmentResolver(id="", name="", icon="", action_economy=ActionEconomy())
    armor = Armor(name="Chainmail", armor_type=ArmorType.MEDIUM, base_ac=10)
    hero.equip(armor)
    hero.unequip("armor")
    assert hero.armor is None


def test_state_change_recomputes_traits(actor: Character) -> None:
    actor.unequip("armor")
    actor.change_job(Fighter)

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 0

    actor.armor = Armor(name="armor", armor_type=ArmorType.MEDIUM, base_ac=5)
    actor.equip_all()

    attrs = actor.attributes
    assert len(attrs.get_modifiers("ac")) == 1
