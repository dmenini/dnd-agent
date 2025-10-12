from logging import getLogger

from agent.models.state import State

log = getLogger(__name__)


class EndCombatNode:
    def __call__(self, state: State) -> State:
        """Advance turn, check victory conditions, and append logs."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        # Advance to next character
        actor = state.current_actor
        state.turn_index += 1

        # End of round → wrap turn
        if state.turn_index >= len(state.turn_order):
            # Reset resources
            actor.attributes.current_movement = actor.speed

            state.round += 1
            state.turn_index = 0
            state.flush_logs()

        # Check if any party has been wiped out
        defeated_parties = [p for p in state.parties.values() if not state.get_party_members(p.id, alive_only=True)]

        # Remove defeated parties from active play
        for defeated in defeated_parties:
            state.append_log(f"Party '{defeated.name}' has been defeated!")

        # Determine if only one party remains
        alive_parties = [
            p
            for p in state.parties.values()
            if p.id not in [d.id for d in defeated_parties] and state.get_party_members(p.id, alive_only=True)
        ]

        # Check victory conditions
        if len(alive_parties) <= 1:
            state.done = True

            if not alive_parties:
                state.append_log("All parties have fallen. It's a draw.")
            else:
                winner = alive_parties[0]

                if winner.is_player_party:
                    state.append_log(f"🎉 The players are victorious! Party '{winner.name}' stands triumphant!")
                else:
                    state.append_log(f"💀 The enemies prevail... Party '{winner.name}' wins the battle.")

            state.flush_logs()

        return state
