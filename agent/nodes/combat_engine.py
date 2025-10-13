from logging import getLogger

from agent.actions.attack import (
    AttackAction,
)
from agent.actions.dash import DashAction
from agent.actions.dodge import DodgeAction
from agent.mechanics.dice_roller import DiceRoller
from agent.models.state import State

ATTACK_ROLL_EXPR = "1d20"

log = getLogger(__name__)


class CombatEngineNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        decision = state.decision
        action = state.action
        actor = state.current_actor

        if not actor.is_alive:
            return state

        if not action or not decision:
            msg = "State is missing action and decision"
            raise ValueError(msg)

        event = f"{actor.name} performs {action.name}: {decision.description}"

        # Handle the main combat actions
        if isinstance(state.action, AttackAction):
            if not decision.target_ids:
                msg = f"No target(s) for action {action.id}"
                raise ValueError(msg)

            targets = [state.characters[tid] for tid in decision.target_ids if tid in state.characters]
            for target in targets:
                event += action.execute(actor=actor, target=target)

        elif isinstance(state.action, DashAction):
            event += action.execute(actor=actor, target=decision.target_position)

        elif isinstance(state.action, DodgeAction):
            event += action.execute(actor=actor, target=None)

        action.finalize(actor)

        state.append_log(event)
        return state
