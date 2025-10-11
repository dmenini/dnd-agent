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
            state.flush_logs()

        if not alive_enemies:
            state.done = True
            if current_actor.is_player:
                msg = "All enemies are defeated! Combat ends."
            else:
                msg = "The player has been defeated! Combat ends."
            state.append_log(msg)
            state.flush_logs()

        return state
