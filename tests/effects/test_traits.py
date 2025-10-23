from agent.character.character import Character
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import Resistance, Trait, Vulnerability
from agent.equipment.armor import Accessory
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability


class CustomEffect(StatusEffect):
    type: EffectType = EffectType.CUSTOM
    duration: int = 2
    _traits: list[Trait] = [
        Resistance(value=0.25, damage_type=DamageType.FIRE),
        Resistance(value=0.25, damage_type=DamageType.COLD),
    ]


def test_same_effects(actor: Character) -> None:
    actor.start_turn()

    effect1 = CustomEffect()
    effect2 = CustomEffect()

    actor.apply_effect(effect1)

    assert actor.status_effects[0].type == EffectType.CUSTOM
    assert actor.status_effects[0].duration == 2
    assert actor.attributes.get_modifiers("resistance.fire")[0].value == 0.25
    assert actor.attributes.get_modifiers("resistance.cold")[0].value == 0.25

    actor.end_turn()
    actor.start_turn()

    assert actor.status_effects[0].type == EffectType.CUSTOM
    assert actor.status_effects[0].duration == 1
    assert actor.attributes.get_modifiers("resistance.fire")[0].value == 0.25
    assert actor.attributes.get_modifiers("resistance.cold")[0].value == 0.25

    actor.apply_effect(effect2)

    assert actor.status_effects[0].type == EffectType.CUSTOM
    assert actor.status_effects[0].duration == 2
    assert len(actor.attributes.get_modifiers("resistance.fire")) == 1
    assert len(actor.attributes.get_modifiers("resistance.cold")) == 1
    assert actor.attributes.get_modifiers("resistance.fire")[0].value == 0.25
    assert actor.attributes.get_modifiers("resistance.cold")[0].value == 0.25


def test_different_traits(actor: Character) -> None:
    value = 0.5
    acc1 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])
    acc2 = Accessory(name="ring", slot="ring", traits=[Vulnerability(value=value, damage_type=DamageType.FIRE)])
    actor.accessories = [acc1, acc2]
    actor.equip_all()

    attrs = actor.attributes
    assert attrs.get_modifiers("resistance.fire")[0].value == value
    assert attrs.get_modifiers("vulnerability.fire")[0].value == value

    assert attrs.damage_resistance(DamageType.FIRE) == DamageResistance(value=value, type=DamageType.FIRE)
    assert attrs.damage_vulnerability(DamageType.FIRE) == DamageVulnerability(value=value, type=DamageType.FIRE)

    actor.start_turn()
    actor.end_turn()

    # Traits don't expire
    assert attrs.get_modifiers("resistance.fire")[0].value == value
    assert attrs.get_modifiers("vulnerability.fire")[0].value == value


def test_same_traits(actor: Character) -> None:
    value = 0.5
    acc1 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])
    acc2 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])
    actor.accessories = [acc1, acc2]
    actor.equip_all()

    attrs = actor.attributes
    assert len(attrs.get_modifiers("resistance.fire")) == 2
    assert attrs.get_modifiers("resistance.fire")[0].value == value
    assert attrs.get_modifiers("resistance.fire")[1].value == value

    assert attrs.damage_resistance(DamageType.FIRE) == DamageResistance(value=value * 2, type=DamageType.FIRE)
