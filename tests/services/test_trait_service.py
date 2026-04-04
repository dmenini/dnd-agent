"""Tests for TraitService."""

from agent.character.character import Character
from agent.effects.traits import TraitBuilder
from agent.models.enums import EventType, FeatureId
from agent.services.trait_service import TraitService


def test_register_passive(fighter: Character) -> None:
    """Test registering a passive trait."""
    initial_count = len(fighter.passives)
    trait = TraitBuilder.attacker_advantage(source_id="test", name="Test Advantage")

    TraitService.register_passive(fighter, trait)

    assert len(fighter.passives) == initial_count + 1
    assert any(p.id == trait.id for p in fighter.passives)


def test_register_passive_idempotent(fighter: Character) -> None:
    """Test that registering the same passive twice doesn't duplicate it."""
    trait = TraitBuilder.attacker_advantage(source_id="test", name="Test Advantage")

    TraitService.register_passive(fighter, trait)
    initial_count = len(fighter.passives)

    # Register again
    TraitService.register_passive(fighter, trait)

    # Should not increase count
    assert len(fighter.passives) == initial_count


def test_register_passive_modifier(fighter: Character) -> None:
    """Test that modifier traits are applied immediately."""
    initial_modifiers = len(fighter.attributes.get_modifiers("crit_roll_bonus"))
    trait = TraitBuilder.critical_roll_bonus(source_id="test", name="Test Crit", value=-1)

    TraitService.register_passive(fighter, trait)

    # Should have added modifier
    assert len(fighter.attributes.get_modifiers("crit_roll_bonus")) > initial_modifiers


def test_unregister_passive(fighter: Character) -> None:
    """Test unregistering a passive trait."""
    trait = TraitBuilder.attacker_advantage(source_id="test", name="Test Advantage")
    TraitService.register_passive(fighter, trait)

    initial_count = len(fighter.passives)

    TraitService.unregister_passive(fighter, feature_id=FeatureId.ATTACKER_ADVANTAGE, source_id="test")

    assert len(fighter.passives) == initial_count - 1
    assert not any(p.id == trait.id for p in fighter.passives)


def test_unregister_passive_removes_modifier(fighter: Character) -> None:
    """Test that unregistering a modifier trait removes the modifier."""
    trait = TraitBuilder.critical_roll_bonus(source_id="test", name="Test Crit", value=-1)
    TraitService.register_passive(fighter, trait)

    initial_modifiers = len(fighter.attributes.get_modifiers("crit_roll_bonus"))

    TraitService.unregister_passive(fighter, feature_id=FeatureId.CRITICAL_ROLL_BONUS, source_id="test")

    # Should have removed modifier
    assert len(fighter.attributes.get_modifiers("crit_roll_bonus")) < initial_modifiers


def test_trigger_event(fighter: Character) -> None:
    """Test triggering events on traits."""

    # Create a mock trait that increments a counter when triggered
    class CounterTrait:
        def __init__(self) -> None:
            self.count = 0
            self.event_type = EventType.TURN_START
            self.priority = 1

        def apply(self, *args: object, **kwargs: object) -> None:
            self.count += 1

    counter = CounterTrait()
    fighter.passives.append(counter)  # type: ignore[arg-type]

    TraitService.trigger_event(fighter, EventType.TURN_START, fighter)

    assert counter.count == 1


def test_trigger_event_respects_priority(fighter: Character) -> None:
    """Test that events are triggered in priority order."""
    order: list[str] = []

    class OrderedTrait:
        def __init__(self, priority: int, label: str) -> None:
            self.priority = priority
            self.label = label
            self.event_type = EventType.TURN_START

        def apply(self, *args: object, **kwargs: object) -> None:
            order.append(self.label)

    # Add in reverse priority order
    fighter.passives.append(OrderedTrait(priority=10, label="low"))  # type: ignore[arg-type]
    fighter.passives.append(OrderedTrait(priority=1, label="high"))  # type: ignore[arg-type]
    fighter.passives.append(OrderedTrait(priority=5, label="mid"))  # type: ignore[arg-type]

    TraitService.trigger_event(fighter, EventType.TURN_START, fighter)

    # Should be triggered in priority order (1, 5, 10)
    assert order == ["high", "mid", "low"]


def test_notify_state_change(fighter: Character) -> None:
    """Test that state changes re-apply dependent traits."""
    # This is harder to test without mocking, but we can at least verify it doesn't crash
    TraitService.notify_state_change(fighter, "equipment.main_hand")
