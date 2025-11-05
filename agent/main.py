import asyncio
import logging
from logging import getLogger
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from agent.logs.log_event import LogLevel
from agent.models.config import Config
from agent.models.state import State
from agent.registration import register_actions, register_traits
from agent.ui.game_ui import GameUI

MAX_ITER = 300
MAP_SIZE = (12, 8)

log = getLogger(__name__)
logging.basicConfig(filename="log.txt", level=logging.INFO)

getLogger("botocore").setLevel(logging.INFO)
getLogger("langchain_aws").setLevel(logging.WARNING)

register_actions()
register_traits()


async def main() -> None:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    state = State()

    state.log.log_event(
        message="Setting up combat simulation.",
        log_type=LogLevel.MAIN,
    )

    ui = GameUI(initial_state=state, config=config)
    await ui.run_async()


if __name__ == "__main__":
    asyncio.run(main())
