from pathlib import Path

import yaml

from agent.graph import build_graph
from agent.models.character import MeleeWeapon, RangeWeapon, Spell, Stats
from agent.models.config import Config
from agent.models.state import Character, State

MAX_ITER = 100


def main() -> None:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    melee = MeleeWeapon(name="Sword", damage_dice="1d6", damage_type="melee")
    range_ = RangeWeapon(name="Bow", damage_dice="1d6", damage_type="range")
    spell = Spell(name="Fire Ball", damage_dice="1d6", damage_type="magic")

    hero = Character(
        id="pc_alfred",
        name="Alfred",
        hp=20,
        pos=(3, 2),
        is_player=True,
        stats=Stats(),
        melee_weapon=melee,
        range_weapon=range_,
        spell=spell,
    )
    orc = Character(id="orc_1", name="Orc Grunt", hp=12, pos=(4, 2), stats=Stats())
    state = State(characters={hero.id: hero, orc.id: orc}, actor_id=hero.id)

    graph = build_graph(config=config.agent)
    print("Starting combat...\n")

    while not state.done and state.turn < MAX_ITER:
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
