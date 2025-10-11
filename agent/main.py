from pathlib import Path

import yaml  # type: ignore[import-untyped]
from langchain_core.runnables import RunnableConfig

from agent.graph import build_graph
from agent.models.character import MeleeWeapon, Party, RangeWeapon, Spell, Stats
from agent.models.config import Config
from agent.models.state import Character, State

MAX_ITER = 100


def main() -> None:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Goblins", is_player_party=False)

    melee = MeleeWeapon(name="Sword", damage_dice="2d6", damage_type="melee")
    range_ = RangeWeapon(name="Bow", damage_dice="1d6", damage_type="range")
    spell = Spell(name="Fire Ball", damage_dice="1d6", damage_type="magic")

    hero = Character(
        id="pc_alfred",
        name="Alfred",
        hp=20,
        pos=(3, 2),
        is_player=True,
        party=party_players,
        stats=Stats(),
        melee_weapon=melee,
        range_weapon=range_,
        spell=spell,
    )
    orc = Character(
        id="orc_1",
        name="Orc Grunt",
        hp=12,
        pos=(4, 2),
        party=party_enemies,
        stats=Stats(),
        melee_weapon=MeleeWeapon(name="Fist", damage_dice="1d3", damage_type="melee"),
    )

    goblin = Character(
        id="goblin_1",
        name="Goblin Dramer",
        hp=6,
        pos=(2, 2),
        party=party_enemies,
        stats=Stats(),
        melee_weapon=MeleeWeapon(name="Dagger", damage_dice="1d5", damage_type="melee"),
    )
    state = State(characters={hero.id: hero, orc.id: orc, goblin.id: goblin},
                  parties={party_players.id: party_players, party_enemies.id: party_enemies})

    graph = build_graph(config=config.agent)

    graph.invoke(state, RunnableConfig(recursion_limit=100))


if __name__ == "__main__":
    main()
