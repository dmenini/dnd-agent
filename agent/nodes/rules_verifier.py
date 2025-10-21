# mypy: disable-error-code="union-attr"

from logging import getLogger

from agent.actions.common.attack import AttackAction
from agent.actions.common.dash import DashAction
from agent.actions.common.move import MovementAction
from agent.logs.events import LogLevel
from agent.models.enums import TargetingType
from agent.models.position import Position
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

        if not isinstance(action, (DashAction, MovementAction)):
            return True, None

        mult = 2 if isinstance(action, DashAction) else 1
        pos = decision.target_position

        if not pos:
            return False, f"No target position specified for action {action.id}"

        if not (Position(x=0, y=0) <= pos < Position(x=state.map_width, y=state.map_height)):
            return (
                False,
                (
                    f"Target position ({pos.x}, {pos.y}) is out of map bounds "
                    f"(0-{state.map_width - 1}, 0-{state.map_height - 1})"
                ),
            )

        dist = actor.distance(pos)
        max_dist = actor.current_speed * mult
        if dist > max_dist:
            return False, f"Position {pos} is out of range ({dist:.1f} > {max_dist})"

        for char in state.alive_characters.values():
            if char.pos == pos:
                return False, f"Position {pos} is already taken by character {char.name}"

        return True, None
