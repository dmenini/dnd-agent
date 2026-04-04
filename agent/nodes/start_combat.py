import random
from logging import getLogger

from agent.logs.log_event import Icon, LogLevel
from agent.models.state import State
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService

log = getLogger(__name__)


class StartCombatNode:
    async def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if not state.turn_order:
            state.log.log_header("Starting combat!")
            self.decide_turn_order(state)

        if state.current_actor is None:
            raise ValueError

        actor = state.current_actor
        if not actor.is_alive:
            return state

        if actor.combat.turn_done:
            actor.log_event(f"Turn {state.round + 1}.{state.turn_index + 1} - {actor.name}", log_type=LogLevel.HEADER)
            CombatService.start_turn(actor)

        state.update_visibility(actor)

        return state

    def decide_turn_order(self, state: State) -> None:
        rolls = []
        for cid, char in state.characters.items():
            # First check roll result - use RollService directly
            init_roll = RollService.initiative_roll(char)
            # Include initiative modifier (DEX mod) as a secondary sort key
            init_mod = char.initiative_modifier
            # Include a random value as a final tie-breaker
            tie_breaker = random.random()  # noqa: S311
            rolls.append((init_roll.total, init_mod, tie_breaker, cid))

        # Sort by total roll, then Dex modifier, then random tie-breaker
        state.turn_order = [cid for _, _, _, cid in sorted(rolls, reverse=True)]
        state.turn_index = 0
        state.log.log_event(
            "Initiative order: " + " → ".join(state.characters[cid].name for cid in state.turn_order),
            log_type=LogLevel.MAIN,
        )
        for roll, char in zip(rolls, state.characters.values(), strict=False):
            char.log_event(
                f"{char.name}: initiative roll={roll[0]}, DEX mod={roll[1]}", icon=Icon.ROLL, log_type=LogLevel.DETAIL
            )
