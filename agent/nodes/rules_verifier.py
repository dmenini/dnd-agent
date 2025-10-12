# mypy: disable-error-code="union-attr"

from logging import getLogger

from agent.models.action import COMBAT_ACTION_TYPES
from agent.models.enums import ActionType
from agent.models.state import State, VerificationResult

log = getLogger(__name__)


class RulesVerifierNode:
    def __init__(self, *, fail_fast: bool = False) -> None:
        """
        fail_fast: if True, stops checking after the first invalid rule.
        """
        self.fail_fast = fail_fast
        self.checks = [
            self.check_action_exists,
            self.check_actor_exists,
            self.check_actor_alive,
            self.check_turn_validity,
            self.check_targets_exist,
            self.check_target_alive,
            self.check_friendly_fire,
            self.check_range,
            # Future checks:
            # self.check_line_of_sight,
            # self.check_spell_slots,
            # self.check_conditions,
        ]

        # TODO: validate multi-target actions match the targeting of the weapon

    def __call__(self, state: State) -> State:
        """Runs all validation checks on the current action."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        reasons: list[str] = []
        valid = True

        if not state.current_actor.is_alive:
            state.verification_result = VerificationResult(valid=valid, reasons=reasons)
            return state

        for check in self.checks:
            ok, reason = check(state)
            if not ok:
                valid = False
                if reason:
                    reasons.append(reason)
                if self.fail_fast:
                    break

        state.verification_result = VerificationResult(valid=valid, reasons=reasons)

        if not state.verification_result.valid:
            event = f"❌ Invalid action {state.action.model_dump_json(exclude={'combat_option'})}\nReasons:\n"
            for reason in state.verification_result.reasons:
                event += f" - {reason}\n"
            state.append_log(event)

        return state

    def check_action_exists(self, state: State) -> tuple[bool, str | None]:
        if not state.action:
            return False, "No action provided"
        return True, None

    def check_actor_exists(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.actor_id not in state.characters:
            return False, f"Actor {action.actor_id} not found"
        return True, None

    def check_actor_alive(self, state: State) -> tuple[bool, str | None]:
        actor = state.characters.get(state.action.actor_id)
        if actor and not actor.is_alive:
            return False, f"{actor.name} is incapacitated or dead"
        return True, None

    def check_turn_validity(self, state: State) -> tuple[bool, str | None]:
        actor = state.characters.get(state.action.actor_id)
        if actor and actor.id != state.current_actor.id:
            return False, "It's not this character's turn"
        return True, None

    def check_targets_exist(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.action_type in COMBAT_ACTION_TYPES:
            if not action.target_ids:
                return False, "Missing targets for combat action"
            for target_id in action.target_ids:
                if target_id not in state.characters:
                    return False, f"Target {target_id} not found"
        return True, None

    def check_target_alive(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.action_type in COMBAT_ACTION_TYPES:
            for target_id in action.target_ids:
                target = state.characters[target_id]
                if not target.is_alive:
                    return False, f"Target {target_id} is already down"
        return True, None

    def check_friendly_fire(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.target_ids and action.action_type in COMBAT_ACTION_TYPES:
            actor = state.current_actor
            for target_id in action.target_ids:
                target = state.characters[target_id]
                if actor.party.id == target.party.id:
                    return False, f"{actor.name} cannot attack ally {target.name}"
        return True, None

    def check_range(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        actor = state.current_actor

        for target_id in action.target_ids:
            target = state.characters[target_id]
            dist = actor.distance(target.pos)
            if dist > action.range:
                return False, f"Target {target.name} is out of range ({dist:.1f} > {action.range})"

        return True, None

    def check_movement(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        actor = state.current_actor

        if action.action_type == ActionType.DASH:
            if not action.target_position:
                return False, f"No target position specified for action {action.action_type}"

            dist = actor.distance(action.target_position)
            max_dist = actor.attributes.current_movement * 2
            if dist > max_dist:
                return False, f"Position {action.target_position} is out of range ({dist:.1f} > {max_dist})"

        return True, None
