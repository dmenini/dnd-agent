from langgraph.runtime import Runtime

from agent.models.state import Context, State, TurnPhase, VerificationResult


class RulesVerifier:
    def __call__(self, state: State, runtime: Runtime[Context]) -> State:
        action = state.action
        reasons = []
        valid = True

        if not action:
            valid = False
            reasons.append("No action provided")

        # Mock logic — later integrate SRD checks
        if action.action_type == "attack" and action.target_id is None:
            valid = False
            reasons.append("Missing target")

        state.verification_result = VerificationResult(valid=valid, reasons=reasons)
        state.phase = TurnPhase.ROLL if state.verification_result.valid else TurnPhase.DECIDE

        return state
