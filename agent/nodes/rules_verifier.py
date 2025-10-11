from logging import getLogger

from agent.models.enums import COMBAT_ACTIONS, ActionType
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
            self.check_target_exists,
            self.check_target_alive,
            self.check_friendly_fire,
            self.check_weapon_equipped,
            self.check_range,
            # Future checks:
            # self.check_line_of_sight,
            # self.check_spell_slots,
            # self.check_conditions,
        ]

    def __call__(self, state: State) -> State:
        """Runs all validation checks on the current action."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        reasons = []
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
            event = f"❌ Invalid action {state.action.model_dump_json()}\nReasons:\n"
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

    def check_target_exists(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.action_type in COMBAT_ACTIONS:
            if not action.target_id:
                return False, "Missing target for combat action"
            if action.target_id not in state.characters:
                return False, f"Target {action.target_id} not found"
        return True, None

    def check_target_alive(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.target_id and action.action_type in COMBAT_ACTIONS:
            target = state.characters[action.target_id]
            if not target.is_alive:
                return False, f"Target {target.name} is already down"
        return True, None

    def check_friendly_fire(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.target_id and action.action_type in COMBAT_ACTIONS:
            actor = state.characters[action.actor_id]
            target = state.characters[action.target_id]
            if actor.party.id == target.party.id:
                return False, f"{actor.name} cannot attack ally {target.name}"
        return True, None

    def check_weapon_equipped(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.action_type not in COMBAT_ACTIONS:
            return True, None  # Skip for non-combat actions

        actor = state.characters[action.actor_id]
        if (
            (action.action_type == ActionType.ATTACK and not actor.melee_weapon)
            or (action.action_type == ActionType.SHOOT and not actor.range_weapon)
            or (action.action_type == ActionType.CAST_SPELL and not actor.spell)
        ):
            return False, f"{actor.name} has no weapon or spell equipped"
        return True, None

    def check_range(self, state: State) -> tuple[bool, str | None]:
        action = state.action
        if action.target_id is None:
            return True, None  # No target — skip range check

        actor = state.characters[action.actor_id]
        target = state.characters[action.target_id]

        weapon = actor.select_weapon(action_type=action.action_type)
        if not weapon:
            return True, None  # no range attribute, skip

        dist = self._distance(actor.pos, target.pos)
        if dist > weapon.range:
            return False, f"Target {target.name} is out of range ({dist:.1f} > {weapon.range})"
        return True, None

    @staticmethod
    def _distance(p1: tuple[int, int], p2: tuple[int, int]) -> float:
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])  # Manhattan distance
