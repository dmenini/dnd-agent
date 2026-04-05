from agent.actions.registry import ActionRegistry
from agent.character.character import Character
from agent.jobs.cleric import Cleric, LifeDomain
from agent.models.context import CombatContext
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_preserve_life(actor: Character, target: Character) -> None:
    """Test Preserve Life using composable action from JSON."""
    JobService.change_job(actor, Cleric.apply_specialization(LifeDomain))
    actor.level = 4  # 4 * 5 = 20 HP to distribute
    target.attributes.hp = 1
    target.attributes.max_hp = lambda level: 50  # Half would be 25

    # Load composable action from registry
    action = ActionRegistry.create(FeatureId.PRESERVE_LIFE)

    # Create a combat context with one target receiving healing
    ctx = CombatContext()
    # Distributed healing needs ctx.hits to know how many targets
    ctx.hits = {target.id: 1}

    action.execute(actor, target, ctx)

    # Should heal for 20 HP (total pool) but capped at 25 (half of max_hp)
    # Since target is at 1 HP, healing should bring them to 21 HP
    assert target.attributes.hp == 21

    # Finalize action consumes resources
    action.finalize(actor)
    assert not action.is_available(actor.action_economy, actor)
