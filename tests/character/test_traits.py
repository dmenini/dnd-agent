from agent.character.attributes import Attributes
from agent.character.character import Character
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.effects.traits import Resistance, Vulnerability
from agent.models.constants import EventType
from agent.models.damage import DamageResistance, DamageType
from agent.models.enums import FeatureId


class CustomEffect(StatusEffect):
    type: EffectType = EffectType.CUSTOM
    duration: int = 2
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.RESISTANCE, kwargs={"value": 0.25, "damage_type": DamageType.FIRE}),
        StatusEffectFeature(ref_id=FeatureId.RESISTANCE, kwargs={"value": 0.25, "damage_type": DamageType.COLD}),
    ]


def assert_modifier(attrs: Attributes, attr_name: str, value: float, source_id: str) -> None:
    mods = attrs.get_modifiers(attr_name)
    assert len(mods) == 1
    mod = mods[0]
    assert mod.value == value
    assert mod.source_id == source_id


def assert_listener(actor: Character, event_type: EventType, source_id: str, count: int = 1) -> None:
    listeners = actor._event_listeners.get(event_type) or []
    assert len([lis for lis in listeners if lis.source_id == source_id]) == count


def assert_passive(actor: Character, feature_id: FeatureId, source_id: str, count: int = 1) -> None:
    ps = [p for p in actor.passives if p.feature_id == feature_id and p.source_id == source_id]
    assert len(ps) == count


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
    trait1 = Resistance(feature_id=FeatureId.RESISTANCE, source_id="ring", value=value, damage_type=DamageType.FIRE)
    trait2 = Vulnerability(
        feature_id=FeatureId.VULNERABILITY, source_id="ring", value=value, damage_type=DamageType.FIRE
    )
    actor.register_passive(trait=trait1)
    actor.register_passive(trait=trait2)

    attrs = actor.attributes

    # Passives
    assert_passive(actor, FeatureId.RESISTANCE, "ring")
    assert_passive(actor, FeatureId.VULNERABILITY, "ring")

    # Listeners
    assert_listener(actor, EventType.MODIFIER, "ring-resistance")
    assert_listener(actor, EventType.MODIFIER, "ring-vulnerability")

    # Modifiers
    assert_modifier(attrs, "resistance.fire", value, "ring-resistance")
    assert_modifier(attrs, "vulnerability.fire", value, "ring-vulnerability")

    # Combined resistance/vulnerability effects
    assert attrs.damage_resistance(DamageType.FIRE).value == value  # type: ignore[union-attr]
    assert attrs.damage_vulnerability(DamageType.FIRE).value == value  # type: ignore[union-attr]

    # Traits persist across turns
    actor.start_turn()
    actor.end_turn()
    assert_modifier(attrs, "resistance.fire", value, "ring-resistance")
    assert_modifier(attrs, "vulnerability.fire", value, "ring-vulnerability")

    # Ensure cleanup
    actor.unregister_passive(FeatureId.RESISTANCE, source_id="ring")
    assert len([p for p in actor.passives if p.feature_id == FeatureId.RESISTANCE]) == 0
    assert len([p for p in actor.passives if p.feature_id == FeatureId.VULNERABILITY]) == 1
    assert_listener(actor, EventType.MODIFIER, "ring-resistance", 0)
    assert_listener(actor, EventType.MODIFIER, "ring-vulnerability", 1)
    assert len(attrs.get_modifiers("resistance.fire")) == 0
    assert len(attrs.get_modifiers("vulnerability.fire")) == 1


def test_same_traits_from_different_sources_stack(actor: Character) -> None:
    value = 0.5
    trait1 = Resistance(feature_id=FeatureId.RESISTANCE, source_id="ring 0", value=value, damage_type=DamageType.FIRE)
    trait2 = Resistance(feature_id=FeatureId.RESISTANCE, source_id="ring 1", value=value, damage_type=DamageType.FIRE)
    actor.register_passive(trait=trait1)
    actor.register_passive(trait=trait2)

    # Passives and listeners
    for i in range(2):
        assert_passive(actor, FeatureId.RESISTANCE, f"ring-{i}")
        assert_listener(actor, EventType.MODIFIER, f"ring-{i}-resistance")

    # Attribute modifiers
    attrs = actor.attributes
    mods = attrs.get_modifiers("resistance.fire")
    assert len(mods) == 2
    for i, mod in enumerate(mods):
        assert mod.value == value
        assert mod.source_id == f"ring-{i}-resistance"

    # Combined total
    total = attrs.damage_resistance(DamageType.FIRE)
    assert total == DamageResistance(value=value * 2, type=DamageType.FIRE)

    # Unequip and cleanup
    source = "ring-0"
    actor.unregister_passive(FeatureId.RESISTANCE, source_id=source)

    assert_passive(actor, FeatureId.RESISTANCE, "ring-0", 0)
    assert_passive(actor, FeatureId.RESISTANCE, "ring-1", 1)
    assert_listener(actor, EventType.MODIFIER, "ring-0-resistance", 0)
    assert_listener(actor, EventType.MODIFIER, "ring-1-resistance", 1)


def test_traits_with_same_feature_id(actor: Character) -> None:
    value = 0.5
    name = "ring"
    trait1 = Resistance(feature_id=FeatureId.RESISTANCE, source_id=name, value=value, damage_type=DamageType.FIRE)
    trait2 = Resistance(feature_id=FeatureId.RESISTANCE, source_id=name, value=value, damage_type=DamageType.COLD)
    actor.register_passive(trait=trait1)
    actor.register_passive(trait=trait2)

    attrs = actor.attributes

    # Two passives, same feature ID, different damage types
    assert len([p for p in actor.passives if p.feature_id == FeatureId.RESISTANCE and p.source_id == name]) == 2
    assert_listener(actor, EventType.MODIFIER, f"{name}-resistance", 2)

    # Modifiers applied correctly
    for dtype in (DamageType.COLD, DamageType.FIRE):
        attr_name = f"resistance.{dtype.value}"
        assert_modifier(attrs, attr_name, value, f"{name}-resistance")
        assert attrs.damage_resistance(dtype) == DamageResistance(value=value, type=dtype)

    # Unequip and cleanup
    actor.unregister_passive(FeatureId.RESISTANCE, source_id=name)
    assert not [p for p in actor.passives if p.feature_id == FeatureId.RESISTANCE]
    assert_listener(actor, EventType.MODIFIER, f"{name}-resistance", 0)
    for dtype in (DamageType.COLD, DamageType.FIRE):
        assert not attrs.get_modifiers(f"resistance.{dtype.value}")


def test_same_traits_same_source_dont_stack(actor: Character) -> None:
    value = 0.5
    name = "ring"
    trait1 = Resistance(feature_id=FeatureId.RESISTANCE, source_id=name, value=value, damage_type=DamageType.FIRE)
    actor.register_passive(trait=trait1)

    attrs = actor.attributes

    # First register
    assert_passive(actor, FeatureId.RESISTANCE, name)
    assert_listener(actor, EventType.MODIFIER, f"{name}-resistance")
    assert_modifier(attrs, "resistance.fire", value, f"{name}-resistance")
    assert attrs.damage_resistance(DamageType.FIRE) == DamageResistance(value=value, type=DamageType.FIRE)

    # Register again - passives may duplicate but modifiers must not
    actor.register_passive(trait=trait1)
    assert len([p for p in actor.passives if p.feature_id == FeatureId.RESISTANCE and p.source_id == name]) == 2
    assert_listener(actor, EventType.MODIFIER, f"{name}-resistance", 2)
    assert len(attrs.get_modifiers("resistance.fire")) == 1
    assert_modifier(attrs, "resistance.fire", value, f"{name}-resistance")

    # Unequip and cleanup
    actor.unregister_passive(FeatureId.RESISTANCE, source_id=name)
    assert not [p for p in actor.passives if p.feature_id == FeatureId.RESISTANCE]
    assert_listener(actor, EventType.MODIFIER, f"{name}-resistance", 0)
    assert not attrs.get_modifiers("resistance.fire")
