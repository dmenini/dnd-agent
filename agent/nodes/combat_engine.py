from langgraph.runtime import Runtime

from agent.models.state import Action, CombatResult, Context, State


class CombatEngine:
    def __call__(self, state: State, runtime: Runtime[Context]) -> State:
        # Mocked — later integrate dice & rules
        action = state.action
        event = f"{action.actor_id} performs {action.action_type} ({action.description or ''})"
        state.combat_result = CombatResult(success=True, events=[event], new_state={"turn_complete": True})
        return state
