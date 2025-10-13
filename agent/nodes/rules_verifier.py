# mypy: disable-error-code="union-attr"

from logging import getLogger

from agent.actions.attack import AttackAction
from agent.actions.dash import DashAction
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
            self.check_targets_exist,
            self.check_targets_alive,
            self.check_targets_valid,
            self.check_friendly_fire,
            self.check_range,
        ]

    def __call__(self, state: State) -> State:
        """Runs all validation checks on the current action."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        valid = True

        if not state.current_actor.is_alive:
            state.verification_result = VerificationResult(valid=valid)
            return state

        if not state.action or not state.decision:
            msg = "State is missing action and decision"
            raise ValueError(msg)

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
            state.append_system_log(f"Validation error: {state.verification_result.reason}")

        return state

    def check_actor_alive(self, state: State) -> tuple[bool, str | None]:
        actor = state.current_actor
        if actor and not actor.is_alive:
            return False, f"{actor.name} is incapacitated or dead"
        return True, None

    def check_targets_exist(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        decision = state.decision
        if isinstance(action, AttackAction):
            if not decision.target_ids:
                return False, "Missing targets for combat action"
            for target_id in decision.target_ids:
                if target_id not in state.characters:
                    return False, f"Target {target_id} not found"
        return True, None

    def check_targets_alive(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        decision = state.decision
        if isinstance(action, AttackAction):
            for target_id in decision.target_ids:
                target = state.characters[target_id]
                if not target.is_alive:
                    return False, f"Target {target_id} is already down"
        return True, None

    def check_targets_valid(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        decision = state.decision
        if (
            isinstance(action, AttackAction)
            and action.targeting == TargetingType.SINGLE
            and len(decision.target_ids) > 1
        ):
            return False, "Cannot have multiple targets for a single target action"
        return True, None

    def check_friendly_fire(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        decision = state.decision
        if decision.target_ids and isinstance(action, AttackAction):
            actor = state.current_actor
            for target_id in decision.target_ids:
                target = state.characters[target_id]
                if actor.party.id == target.party.id:
                    return False, f"{actor.name} cannot attack ally {target.name}"
        return True, None

    def check_range(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        actor = state.current_actor
        decision = state.decision

        for target_id in decision.target_ids:
            target = state.characters[target_id]
            dist = actor.distance(target.pos)
            if dist > action.range:
                return False, f"Target {target.name} is out of range ({dist:.1f} > {action.range})"

        return True, None

    def check_movement(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        actor = state.current_actor
        decision = state.decision

        if isinstance(action, DashAction):
            if not decision.target_position:
                return False, f"No target position specified for action {action.action_type}"

            dist = actor.distance(decision.target_position)
            max_dist = actor.attributes.current_movement * 2
            if dist > max_dist:
                return False, f"Position {decision.target_position} is out of range ({dist:.1f} > {max_dist})"

        return True, None
