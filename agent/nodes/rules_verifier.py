from agent.models.enums import ActionType
from agent.models.state import State, VerificationResult


class RulesVerifierNode:
    def __call__(self, state: State) -> State:
        action = state.action
        reasons = []
        valid = True

        if not action:
            valid = False
            reasons.append("No action provided")

        # Mock logic — later integrate SRD checks
        if action and action.action_type == ActionType.ATTACK and action.target_id is None:
            valid = False
            reasons.append("Missing target")

        state.verification_result = VerificationResult(valid=valid, reasons=reasons)

        return state
