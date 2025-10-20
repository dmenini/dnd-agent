from agent.actions.jobs.fighter import SecondWindAction
from agent.actions.registry import ActionRegistry
from agent.models.constants import SECOND_WIND_ID


def register_actions() -> None:
    ActionRegistry.register(SECOND_WIND_ID, SecondWindAction)
