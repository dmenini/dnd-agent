from logging import getLogger

from agent.logs.log_event import Icon, LogLevel
from agent.models.state import State

log = getLogger(__name__)


class EndCombatNode:
    async def __call__(self, state: State) -> State:
        """Advance turn, check victory conditions, and append logs."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        actor = state.current_actor

        if not state.map:
            msg = "Map not initialized"
            raise ValueError(msg)

        state.map.update_map(characters=state.characters)

        # Advance to next character if resources exhausted
        if not actor.is_alive or not actor.has_resources():
            if actor.is_alive:
                actor.end_turn()
            state.turn_index += 1

        # End of round
        if state.turn_index >= len(state.characters):
            state.log.log_event(f"Turn {state.round + 1} over!", log_type=LogLevel.SYSTEM)

            # Reset resources
            for char in state.alive_characters.values():
                char.end_round()

            state.round += 1
            state.turn_index = 0

        self._check_victory_conditions(state)

        return state

    def _check_victory_conditions(self, state: State) -> None:
        # Check if any party has been wiped out
        defeated_parties = [p for p in state.parties.values() if not state.get_party_members(p.id, alive_only=True)]
        defeated_parties_ids = [p.id for p in defeated_parties]
        for defeated in defeated_parties:
            state.log.log_event(f"Party '{defeated.name}' has been defeated!", icon=Icon.DEATH, log_type=LogLevel.MAIN)

        # Determine if only one party remains
        alive_parties = [p for p in state.parties.values() if p.id not in defeated_parties_ids]

        # Check victory conditions
        if len(alive_parties) <= 1:
            state.done = True

            if not alive_parties:
                state.log.log_event("All parties have fallen. It's a draw.", log_type=LogLevel.SYSTEM)
            else:
                winner = alive_parties[0]

                if winner.is_player_party:
                    state.log.log_event(
                        f"The players are victorious! Party '{winner.name}' stands triumphant!",
                        log_type=LogLevel.SYSTEM,
                    )
                else:
                    state.log.log_event(
                        f"The enemies prevail... Party '{winner.name}' wins the battle.",
                        log_type=LogLevel.SYSTEM,
                    )
