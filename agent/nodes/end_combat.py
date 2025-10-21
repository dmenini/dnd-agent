from logging import getLogger

from agent.logs.events import Icon, LogLevel
from agent.models.state import State

log = getLogger(__name__)


class EndCombatNode:
    def __call__(self, state: State) -> State:
        """Advance turn, check victory conditions, and append logs."""
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        actor = state.current_actor

        # Advance to next character if resources exhausted
        # TODO: Improve this by avoid looping over dead characters, just remove them from initiative order
        if not actor.is_alive or not actor.has_resources():
            actor.end_turn()
            state.turn_index += 1

        # End of round
        if state.turn_index >= len(state.characters):
            state.log.log_event(f"Turn {state.round + 1} over!", event_type=LogLevel.SYSTEM)

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
            state.log.log_event(f"Party '{defeated.name}' has been defeated!", icon=Icon.DEATH)

        # Determine if only one party remains
        alive_parties = [p for p in state.parties.values() if p.id not in defeated_parties_ids]

        # Check victory conditions
        if len(alive_parties) <= 1:
            state.done = True

            if not alive_parties:
                state.log.log_event("All parties have fallen. It's a draw.", event_type=LogLevel.SYSTEM)
            else:
                winner = alive_parties[0]

                if winner.is_player_party:
                    state.log.log_event(
                        f"The players are victorious! Party '{winner.name}' stands triumphant!",
                        event_type=LogLevel.SYSTEM,
                    )
                else:
                    state.log.log_event(
                        f"The enemies prevail... Party '{winner.name}' wins the battle.",
                        event_type=LogLevel.SYSTEM,
                    )
