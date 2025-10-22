import logging
from logging import getLogger
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from langchain_core.runnables import RunnableConfig

from agent.ai.graph import build_graph
from agent.ai.map_generator import build_map_generator
from agent.character.attributes import Attributes
from agent.character.character import Party
from agent.effects.status_effects.poisoned import Poisoned
from agent.effects.status_effects.stunned import Stunned
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponType
from agent.jobs.fighter import Fighter
from agent.jobs.mage import Mage
from agent.logs.events import LogLevel
from agent.models.config import Config
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import Character, State
from agent.registration import register_actions, register_traits

MAX_ITER = 150
MAP_SIZE = 10

log = getLogger(__name__)
logging.basicConfig(level=logging.INFO)

getLogger("botocore").setLevel(logging.INFO)
getLogger("langchain_aws").setLevel(logging.WARNING)

register_actions()
register_traits()


def main() -> None:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    state = State()

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Goblins", is_player_party=False)

    state.log.log_event(
        message=f"Setting up combat simulation: {party_players.name} vs {party_enemies.name}",
        event_type=LogLevel.SYSTEM
    )

    sword = MeleeWeapon(
        name="Sword",
        description="Heavy sword that may stun the enemy",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        range=2,
        targeting=TargetingType.SINGLE,
        effects=[Stunned(duration=1)],
    )
    bow = RangedWeapon(
        name="Bow",
        damage_dice="1d6",
        damage_type=DamageType.PIERCING,
        weapon_type=WeaponType.SIMPLE_RANGE,
        range=10,
        targeting=TargetingType.SINGLE,
    )
    dagger = MeleeWeapon(
        name="Dagger",
        description="Poisonous dagger",
        damage_dice="1d5",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.SIMPLE_MELEE,
        range=1,
        targeting=TargetingType.SINGLE,
        effects=[Poisoned(duration=3, damage=1)],
    )

    hero = Character(
        id="pc_alfred",
        name="Alfred",
        icon="🤡",
        job=Fighter,
        attributes=Attributes(base_hp=20),
        is_player=True,
        party=party_players,
        main_hand=sword,
        ranged=bow,
    )
    orc = Character(
        id="orc_1",
        name="Orc Grunt",
        icon="👹",
        job=Fighter,
        party=party_enemies,
    )
    goblin = Character(
        id="goblin_1",
        name="Goblin Dramer",
        icon="🧌",
        job=Mage,
        party=party_enemies,
        main_hand=dagger,
    )

    # TODO: log character summary

    state.log.log_event(
        message=f"Generating combat map of size {MAP_SIZE}x{MAP_SIZE}",
        event_type=LogLevel.SYSTEM
    )

    gen = build_map_generator(config.agent)
    map = gen.invoke({
        "width": MAP_SIZE,
        "height": MAP_SIZE,
        "players": [hero.id],
        "enemies": [goblin.id, orc.id],
    })
    if not isinstance(map, GameMap):
        raise TypeError

    state.map = map
    # Players choose their icon
    map.icons[hero.id] = hero.icon

    # Set positions
    hero.pos = map.characters[hero.id]
    orc.pos = map.characters[orc.id]
    goblin.pos = map.characters[goblin.id]

    state.characters = {hero.id: hero, orc.id: orc, goblin.id: goblin}
    state.parties = {party_players.id: party_players, party_enemies.id: party_enemies}

    graph = build_graph(config=config.agent)

    graph.invoke(state, RunnableConfig(recursion_limit=MAX_ITER))


if __name__ == "__main__":
    main()
