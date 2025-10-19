from logging import getLogger

from agent.actions.attack import (
    AttackAction,
)
from agent.actions.dash import DashAction
from agent.actions.dodge import DodgeAction
from agent.actions.move import MovementAction
from agent.actions.spell import SupportSpellAction
from agent.actions.wait import WaitAction
from agent.mechanics.dice_roller import DiceRoller
from agent.models.context import CombatContext
from agent.models.state import State

ATTACK_ROLL_EXPR = "1d20"

log = getLogger(__name__)


class CombatEngineNode:
    def __init__(self, dice: DiceRoller) -> None:
        self._dice = dice

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if not state.action or not state.decision:
            return state

        decision = state.decision
        action = state.action
        actor = state.current_actor

        if not actor.is_alive:
            return state

        ctx = CombatContext(dice=self._dice)

        # Handle the main combat actions
        if isinstance(state.action, (AttackAction, SupportSpellAction)):
            if not decision.target_ids:
                msg = f"No target(s) for action {action.id}"
                raise ValueError(msg)

            targets = [state.characters[tid] for tid in decision.target_ids if tid in state.characters]
            for target in targets:
                actor.log_event(f"{actor.name} performs {action.name} on target {target.name}: {action.description}")
                action.execute(actor=actor, target=target, ctx=ctx)

        elif isinstance(state.action, (DashAction, MovementAction)):
            actor.log_event(f"{actor.name} performs {action.name} to position {decision.target_position}")
            action.execute(actor=actor, target=decision.target_position, ctx=ctx)

        elif isinstance(state.action, DodgeAction):
            actor.log_event(f"{actor.name} performs {action.name} on self")
            action.execute(actor=actor, target=None, ctx=ctx)

        elif isinstance(state.action, WaitAction):
            actor.log_event(f"{actor.name} performs {action.name} to pass the turn")
            action.execute(actor=actor, target=None, ctx=ctx)

        action.finalize(actor)

        return state
