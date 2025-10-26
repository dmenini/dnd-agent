import random
from logging import getLogger

from agent.character.stats import StatType
from agent.logs.events import LogLevel
from agent.mechanics.dice_roller import DiceRoller
from agent.models.state import State

log = getLogger(__name__)


class StartCombatNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        state.log.log_header("Starting combat!")

        rolls = []
        for cid, char in state.characters.items():
            # First check roll result
            init_roll = char.initiative_roll()
            # Include Dexterity modifier as a secondary sort key
            dex_mod = char.attributes.stat_modifier(StatType.DEX)
            # Include a random value as a final tie-breaker
            tie_breaker = random.random()  # noqa: S311
            rolls.append((init_roll.total, dex_mod, tie_breaker, cid))

        # Sort by total roll, then Dex modifier, then random tie-breaker
        state.turn_order = [cid for _, _, _, cid in sorted(rolls, reverse=True)]
        state.turn_index = 0
        state.log.log_event(
            "Initiative order: " + " → ".join(state.characters[cid].name for cid in state.turn_order),
            log_type=LogLevel.SYSTEM,
        )

        return state
