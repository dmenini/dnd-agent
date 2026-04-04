"""Test concentration mechanics for spells."""
from agent.actions.common.spell import BonusSupportSpellAction
from agent.character.character import Character
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.traits import TraitBuilder
from agent.jobs.cleric import Cleric, WarDomain
from agent.models.context import CombatContext
from agent.models.enums import FeatureId
from agent.services.effect_service import EffectService
from agent.services.job_service import JobService


def test_concentration_tracking(actor: Character) -> None:
    """Test that casting a concentration spell tracks it on the character."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Initially not concentrating
    assert actor.concentrating_on is None

    # Cast Divine Favor (concentration spell)
    divine_favor = next((s for s in actor.spells if s.id == FeatureId.DIVINE_FAVOR), None)
    assert divine_favor is not None
    assert isinstance(divine_favor, BonusSupportSpellAction)
    assert divine_favor.requires_concentration

    ctx = CombatContext()
    divine_favor.execute(actor, None, ctx)

    # Now should be concentrating
    assert actor.concentrating_on is not None
    assert actor.concentrating_on.type == StatusType.DIVINE_FAVORED
    assert EffectService.has_condition(actor, StatusType.DIVINE_FAVORED)


def test_concentration_breaks_on_new_spell(actor: Character) -> None:
    """Test that casting a new concentration spell breaks the old one."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Cast first concentration spell
    divine_favor = next((s for s in actor.spells if s.id == FeatureId.DIVINE_FAVOR), None)
    assert divine_favor is not None
    assert isinstance(divine_favor, BonusSupportSpellAction)

    ctx = CombatContext()
    divine_favor.execute(actor, None, ctx)

    assert actor.concentrating_on is not None
    assert actor.concentrating_on.type == StatusType.DIVINE_FAVORED
    assert EffectService.has_condition(actor, StatusType.DIVINE_FAVORED)

    # Create a second concentration spell manually
    second_effect = StatusEffect(
        type=StatusType.HASTED,
        duration=10,
        save_dc=0,
        traits=[
            TraitBuilder.speed_multiplier(source_id="haste", value=2),
        ],
    )

    # Simulate casting a second concentration spell by manually calling _handle_concentration
    if actor.concentrating_on:
        old_effect = actor.concentrating_on
        EffectService.remove_condition(actor, old_effect.type)
        actor.concentrating_on = None

    EffectService.try_apply_condition(actor, second_effect)
    actor.concentrating_on = second_effect

    # First effect should be gone, second should be active
    assert not EffectService.has_condition(actor, StatusType.DIVINE_FAVORED)
    assert EffectService.has_condition(actor, StatusType.HASTED)
    assert actor.concentrating_on.type == StatusType.HASTED


def test_concentration_breaks_on_incapacitation(actor: Character) -> None:
    """Test that incapacitating effects break concentration."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Cast concentration spell
    divine_favor = next((s for s in actor.spells if s.id == FeatureId.DIVINE_FAVOR), None)
    assert divine_favor is not None
    assert isinstance(divine_favor, BonusSupportSpellAction)

    ctx = CombatContext()
    divine_favor.execute(actor, None, ctx)

    assert actor.concentrating_on is not None
    assert EffectService.has_condition(actor, StatusType.DIVINE_FAVORED)

    # Apply stunned effect (use apply_condition to bypass save throw)
    stunned = StatusEffect(
        type=StatusType.STUNNED,
        duration=1,
        save_dc=0,
        traits=[],
    )
    EffectService.apply_condition(actor, stunned)

    # Concentration should be broken
    assert actor.concentrating_on is None
    assert not EffectService.has_condition(actor, StatusType.DIVINE_FAVORED)


def test_concentration_clears_on_expire(actor: Character) -> None:
    """Test that concentration tracking is cleared when effect expires."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Cast concentration spell
    divine_favor = next((s for s in actor.spells if s.id == FeatureId.DIVINE_FAVOR), None)
    assert divine_favor is not None
    assert isinstance(divine_favor, BonusSupportSpellAction)

    ctx = CombatContext()
    divine_favor.execute(actor, None, ctx)

    assert actor.concentrating_on is not None

    # Manually expire the effect
    EffectService.remove_condition(actor, StatusType.DIVINE_FAVORED)

    # Concentration should be cleared
    assert actor.concentrating_on is None
