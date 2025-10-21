from logging import getLogger

from agent.actions.common.attack import (
    AttackAction,
)
from agent.actions.common.dash import DashAction
from agent.actions.common.dodge import DodgeAction
from agent.actions.common.move import MovementAction
from agent.actions.common.spell import SupportSpellAction
from agent.actions.common.wait import WaitAction
from agent.models.state import State

ATTACK_ROLL_EXPR = "1d20"

log = getLogger(__name__)


class CombatEngineNode:
    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if not state.action or not state.decision:
            return state

        decision = state.decision
        action = state.action
        actor = state.current_actor

        if not actor.is_alive:
            return state

        # Handle the main combat actions
        if isinstance(state.action, (AttackAction, SupportSpellAction)):
            if not decision.target_ids:
                msg = f"No target(s) for action {action.id}"
                raise ValueError(msg)

            targets = [state.characters[tid] for tid in decision.target_ids if tid in state.characters]
            for target in targets:
                actor.log_event(f"{actor.name} performs {action.name} on target {target.name}: {action.description}")
                action.execute(actor=actor, target=target)

        elif isinstance(state.action, (DashAction, MovementAction)):
            actor.log_event(f"{actor.name} performs {action.name} to position {decision.target_position}")
            action.execute(actor=actor, target=decision.target_position)

        elif isinstance(state.action, DodgeAction):
            actor.log_event(f"{actor.name} performs {action.name} on self")
            action.execute(actor=actor, target=None)

        elif isinstance(state.action, WaitAction):
            actor.log_event(f"{actor.name} performs {action.name} to pass the turn")
            action.execute(actor=actor, target=None)

        action.finalize(actor)

        return state
