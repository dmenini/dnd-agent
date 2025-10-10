from langgraph.runtime import Runtime

from agent.models.state import Context, State, VerificationResult


class RulesVerifier:
    def __call__(self, state: State, runtime: Runtime[Context]) -> State:
        action, obs = state.action, state.observation
        # Mock logic — later integrate SRD checks
        if action.action_type == "attack" and action.target_id is None:
            state.verification_result = VerificationResult(valid=False, reasons=["Missing target"])
        else:
            state.verification_result = VerificationResult(valid=True)

        return state
