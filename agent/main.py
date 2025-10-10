from pathlib import Path
from pprint import pprint

import yaml

from agent.graph import build_graph
from agent.models.config import Config
from agent.models.state import Observation, State


def main():
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    graph = build_graph(config=config.agent)

    # Sample observation
    obs = Observation(
        turn=1,
        visible_entities=[{"id": "orc_1", "hp": 12, "pos": [4, 2]}],
        last_event=None,
        pc_state={"id": "pc_alfred", "hp": 18, "pos": [3, 2]},
    )
    init_state = State(observation=obs)

    final_state = graph.invoke(init_state)

    pprint(final_state)


if __name__ == "__main__":
    main()
