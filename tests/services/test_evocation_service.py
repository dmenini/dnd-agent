"""Tests for EvocationService."""

from agent.character.character import Character
from agent.character.resources import ActionEconomy
from agent.effects.evocations.base import Evocation
from agent.jobs.feature import JobFeature
from agent.models.enums import FeatureId
from agent.services.evocation_service import EvocationService


def test_add_evocation(wizard: Character) -> None:
    """Test adding an evocation."""
    initial_count = len(wizard.evocations)

    evocation = Evocation(
        source_id="test_evocation",
        name="Test Evocation",
        duration=3,
        action_economy=ActionEconomy(),
    )

    EvocationService.add_evocation(wizard, evocation)

    assert len(wizard.evocations) == initial_count + 1
    assert any(e.source_id == "test_evocation" for e in wizard.evocations)


def test_add_evocation_replaces_existing(wizard: Character) -> None:
    """Test that adding evocation with same source_id replaces existing."""
    evocation1 = Evocation(
        source_id="test_evocation",
        name="Evocation 1",
        duration=2,
        action_economy=ActionEconomy(),
    )
    evocation2 = Evocation(
        source_id="test_evocation",
        name="Evocation 2",
        duration=5,
        action_economy=ActionEconomy(),
    )

    EvocationService.add_evocation(wizard, evocation1)
    assert len(wizard.evocations) == 1

    EvocationService.add_evocation(wizard, evocation2)

    # Should still have only 1 evocation
    assert len(wizard.evocations) == 1
    # But with new duration
    assert wizard.evocations[0].duration == 5
    assert wizard.evocations[0].name == "Evocation 2"


def test_remove_evocation(wizard: Character) -> None:
    """Test removing an evocation."""
    evocation = Evocation(
        source_id="test_evocation",
        name="Test Evocation",
        duration=3,
        action_economy=ActionEconomy(),
    )

    EvocationService.add_evocation(wizard, evocation)
    assert len(wizard.evocations) == 1

    EvocationService.remove_evocation(wizard, "test_evocation")

    assert len(wizard.evocations) == 0


def test_expire_evocations(wizard: Character) -> None:
    """Test that evocations expire when duration reaches 0."""
    evocation = Evocation(
        source_id="test_evocation",
        name="Test Evocation",
        duration=2,
        action_economy=ActionEconomy(),
    )

    EvocationService.add_evocation(wizard, evocation)

    # First expiration
    EvocationService.expire_evocations(wizard)
    assert len(wizard.evocations) == 1
    assert wizard.evocations[0].duration == 1

    # Second expiration
    EvocationService.expire_evocations(wizard)
    assert len(wizard.evocations) == 0


def test_expire_evocations_restores_action_economy(wizard: Character) -> None:
    """Test that expire_evocations restores evocation action economy."""
    evocation = Evocation(
        source_id="test_evocation",
        name="Test Evocation",
        duration=3,
        action_economy=ActionEconomy(),
    )
    # Exhaust its actions
    evocation.action_economy.standard_actions = 0
    evocation.action_economy.bonus_actions = 0

    EvocationService.add_evocation(wizard, evocation)

    EvocationService.expire_evocations(wizard)

    # Action economy should be restored
    assert wizard.evocations[0].action_economy.standard_actions == 1
    assert wizard.evocations[0].action_economy.bonus_actions == 1


def test_evocation_actions_with_features(wizard: Character) -> None:
    """Test getting actions from evocations with features."""
    # Create evocation with a feature
    feature = JobFeature(
        ref_id=FeatureId.SECOND_WIND,
        name="Test Feature",
        description="Test feature description",
        level_required=1,
    )
    evocation = Evocation(
        source_id="test_evocation",
        name="Test Evocation",
        duration=3,
        action_economy=ActionEconomy(),
        features=[feature],
    )

    EvocationService.add_evocation(wizard, evocation)

    actions = EvocationService.evocation_actions(wizard)

    assert len(actions) > 0


def test_evocation_actions_empty(wizard: Character) -> None:
    """Test getting actions when no evocations exist."""
    actions = EvocationService.evocation_actions(wizard)

    assert actions == []


def test_multiple_evocations(wizard: Character) -> None:
    """Test managing multiple evocations."""
    evocation1 = Evocation(
        source_id="evocation1",
        name="Evocation 1",
        duration=2,
        action_economy=ActionEconomy(),
    )
    evocation2 = Evocation(
        source_id="evocation2",
        name="Evocation 2",
        duration=3,
        action_economy=ActionEconomy(),
    )

    EvocationService.add_evocation(wizard, evocation1)
    EvocationService.add_evocation(wizard, evocation2)

    assert len(wizard.evocations) == 2

    # Expire evocations
    EvocationService.expire_evocations(wizard)
    assert len(wizard.evocations) == 2  # Both still active

    # Expire again
    EvocationService.expire_evocations(wizard)
    assert len(wizard.evocations) == 1  # First one expired

    # Expire once more
    EvocationService.expire_evocations(wizard)
    assert len(wizard.evocations) == 0  # Both expired
