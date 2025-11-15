from agent.actions.jobs.barbarian import RageAction
from agent.character.character import Character
from agent.effects.status_effects.enraged import Enraged
from agent.jobs.barbarian import Barbarian
from agent.models.context import CombatContext
from agent.models.enums import FeatureId


def test_rage(actor: Character, target: Character) -> None:
    actor.change_job(Barbarian)
    target.attributes.hp = 5

    action = RageAction(id=FeatureId.RAGE.value, description="", damage_bonus=4)

    action.execute(actor, target, ctx=CombatContext())

    assert isinstance(actor.status_effects[0], Enraged)
    assert actor.status_effects[0].duration == 1

    trait = next(p for p in actor.passives if p.feature_id == FeatureId.DAMAGE_BONUS_WITH_MELEE_WEAPON)
    assert trait.effect_params == {"value": 4}

    assert len([p for p in actor.passives if p.feature_id.startswith("resistance")]) == 3

    # Finalize action consumes the bonus use
    action.finalize(actor)
    assert action.is_available(actor.action_economy) is False
    assert action.current_uses == 1
