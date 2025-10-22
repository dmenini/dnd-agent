# mypy: disable-error-code="union-attr"

from logging import getLogger

from agent.actions.common.attack import AttackAction
from agent.actions.common.dash import DashAction
from agent.actions.common.move import MovementAction
from agent.logs.events import LogLevel
from agent.models.enums import TargetingType
from agent.models.state import State, VerificationResult

log = getLogger(__name__)


class RulesVerifierNode:
    def __init__(self, *, fail_fast: bool = False) -> None:
        """
        fail_fast: if True, stops checking after the first invalid rule.
        """
        self.fail_fast = fail_fast
        self.checks = [
            self.check_actor_alive,
            self.check_targets_valid,
            self.check_targets_exist,
            self.check_targets_alive,
            self.check_friendly_fire,
            self.check_range,
            self.check_movement,
        ]

    def __call__(self, state: State) -> State:
        """Runs all validation checks on the current action."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        valid = True

        if not state.current_actor.is_alive:
            state.verification_result = VerificationResult(valid=valid)
            return state

        if not state.action or not state.decision:
            state.verification_result = VerificationResult(valid=valid)
            return state

        reasons = []
        for check in self.checks:
            ok, reason = check(state)
            if not ok:
                valid = False
                if reason:
                    reasons.append(reason)
                if self.fail_fast:
                    break

        state.verification_result = VerificationResult(valid=valid, reason="; ".join(reasons), input=state.action)
        if not valid:
            state.log.log_event(f"Validation error: {state.verification_result.reason}", event_type=LogLevel.SYSTEM)

        return state

    def check_actor_alive(self, state: State) -> tuple[bool, str | None]:
        actor = state.current_actor
        if actor and not actor.is_alive:
            return False, f"{actor.name} is incapacitated or dead"
        return True, None

    def check_targets_valid(self, state: State) -> tuple[bool, str | None]:
        if not state.action:
            return True, None
        if state.action.targeting == TargetingType.SELF:
            return state.decision.validate_self_targeting(actor_id=state.current_actor.id)
        if state.action.targeting == TargetingType.AREA:
            return state.decision.validate_area_targeting()
        if state.action.targeting == TargetingType.SINGLE:
            return state.decision.validate_single_targeting(action=state.action)
        if state.action.targeting == TargetingType.MULTI:
            return state.decision.validate_multi_targeting(action=state.action)
        return True, None

    def check_targets_exist(self, state: State) -> tuple[bool, str | None]:
        return state.decision.validate_targets_exist(state.characters)

    def check_targets_alive(self, state: State) -> tuple[bool, str | None]:
        return state.decision.validate_targets_alive(state.characters)

    def check_friendly_fire(self, state: State) -> tuple[bool, str | None]:
        if not isinstance(state.action, AttackAction):
            return True, None
        return state.decision.validate_friendly_fire(actor=state.current_actor, characters=state.characters)

    def check_range(self, state: State) -> tuple[bool, str | None]:
        if not hasattr(state.action, "range"):
            return True, None
        return state.decision.validate_range(
            actor=state.current_actor,
            characters=state.characters,
            available_movement=state.action.range,
        )

    def check_movement(self, state: State) -> tuple[bool, str | None]:
        if not isinstance(state.action, (DashAction, MovementAction)):
            return True, None
        if not state.map:
            raise ValueError
        return state.decision.validate_movement(
            actor=state.current_actor,
            action=state.action,
            game_map=state.map,
        )
