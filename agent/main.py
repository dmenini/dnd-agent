from pathlib import Path
from pprint import pprint

import yaml

from agent.graph import build_graph
from agent.models.config import Config
from agent.models.state import Character, State


def main():
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    hero = Character(id="pc_alfred", name="Alfred", hp=20, pos=(3, 2), is_player=True)
    orc = Character(id="orc_1", name="Orc Grunt", hp=12, pos=(4, 2))
    state = State(characters={hero.id: hero, orc.id: orc}, actor_id=hero.id)

    graph = build_graph(config=config.agent)
    print("Starting combat...\n")

    while not state.done and state.turn < 10:
        state = State.model_validate(graph.invoke(state))
        print(f"\n--- Turn {state.turn} ---")
        for event in state.event_log:
            print(event)

        state.event_log = []

        if state.done:
            print("Combat ended!")
            break


if __name__ == "__main__":
    main()
