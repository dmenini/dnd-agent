from logging import getLogger

from agent.logs.events import EventType
from agent.mechanics.dice_roller import DiceRoller
from agent.models.state import State

log = getLogger(__name__)


class StartCombatNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        state.append_title_log("Starting combat!", event_type=EventType.HEADER)

        rolls = []
        for cid, char in state.characters.items():
            init_roll = char.initiative_roll()
            rolls.append((init_roll.total, cid))

        state.turn_order = [cid for _, cid in sorted(rolls, reverse=True)]
        state.turn_index = 0
        state.log_event(
            "Initiative order: " + " → ".join(state.characters[cid].name for cid in state.turn_order),
            event_type=EventType.SYSTEM,
        )

        return state
