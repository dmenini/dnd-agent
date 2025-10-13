from logging import getLogger

from agent.models.state import State

log = getLogger(__name__)


class EndCombatNode:
    def __call__(self, state: State) -> State:
        """Advance turn, check victory conditions, and append logs."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        actor = state.current_actor

        # Advance to next character if resources exhausted
        if not actor.is_alive or not actor.has_resources():
            state.turn_index += 1

        # End of round → wrap turn
        if state.turn_index >= len(state.characters):
            # Reset resources
            for char in state.alive_characters.values():
                char.attributes.current_movement = actor.speed
                char.action_economy.restore_all()
                char.elapse_conditions()

            state.round += 1
            state.turn_index = 0

        self._check_victory_conditions(state)

        return state

    def _check_victory_conditions(self, state: State) -> None:
        # Check if any party has been wiped out
        defeated_parties = [p for p in state.parties.values() if not state.get_party_members(p.id, alive_only=True)]
        defeated_parties_ids = [p.id for p in defeated_parties]
        for defeated in defeated_parties:
            state.append_system_log(f"Party '{defeated.name}' has been defeated!")

        # Determine if only one party remains
        alive_parties = [p for p in state.parties.values() if p.id not in defeated_parties_ids]

        # Check victory conditions
        if len(alive_parties) <= 1:
            state.done = True

            if not alive_parties:
                state.append_system_log("All parties have fallen. It's a draw.")
            else:
                winner = alive_parties[0]

                if winner.is_player_party:
                    state.append_system_log(f"🎉 The players are victorious! Party '{winner.name}' stands triumphant!")
                else:
                    state.append_system_log(f"💀 The enemies prevail... Party '{winner.name}' wins the battle.")
