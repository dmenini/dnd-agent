from agent.models.enums import ActionType, COMBAT_ACTIONS
from agent.models.state import State, VerificationResult


class RulesVerifierNode:
    def __call__(self, state: State) -> State:
        action = state.action
        reasons = []
        valid = True

        if not action:
            valid = False
            reasons.append("No action provided")

        if action.action_type in COMBAT_ACTIONS and action.target_id is None:
            valid = False
            reasons.append("Missing target")

        state.verification_result = VerificationResult(valid=valid, reasons=reasons)

        return state
