
from agent.models.state import State


class EndCombatNode:
    def __call__(self, state: State) -> State:
        """Append event, advance turn, and check victory conditions."""
        current_actor = state.current_actor
        alive_enemies = [c for c in state.alive_characters.values() if c.id != current_actor.id]

        state.turn_index += 1
        if state.turn_index == len(state.turn_order):
            state.turn += 1
            state.turn_index = 0
            state.event_log.insert(0, f"\n--- Turn {state.turn} ---")
            state.flush_logs()

        if not alive_enemies:
            state.done = True
            state.event_log.insert(0, f"\n--- Turn {state.turn} ---")
            state.event_log.append("All enemies are defeated! Combat ends.")
            state.flush_logs()

        return state
