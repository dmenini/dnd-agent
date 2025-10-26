import logging
from logging import getLogger
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from langchain_core.runnables import Runnable, RunnableConfig

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

MAX_ITER = 300
MAP_SIZE = 10

log = getLogger(__name__)
logging.basicConfig(level=logging.INFO)

getLogger("botocore").setLevel(logging.INFO)
getLogger("langchain_aws").setLevel(logging.WARNING)

register_actions()
register_traits()


def generate_game_map(chain: Runnable, enemies: list[str], players: list[str]) -> GameMap:
    user_template = f"These are the characters that take part in the combat:\nEnemies: {enemies}\nPlayers: {players}"
    game_map = chain.invoke(
        {
            "width": MAP_SIZE,
            "height": MAP_SIZE,
            "input": user_template,
        }
    )
    if not isinstance(game_map, GameMap):
        raise TypeError
    return game_map


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
        log_type=LogLevel.SYSTEM,
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
        effects=[Poisoned(duration=3)],
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
    ally = Character(
        id="pc_alice",
        name="Alice",
        icon="👧",
        job=Mage,
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

    state.log.log_event(message=f"Generating combat map of size {MAP_SIZE}x{MAP_SIZE}", log_type=LogLevel.SYSTEM)

    gen = build_map_generator(config.agent)
    game_map = generate_game_map(gen, enemies=[goblin.id, orc.id], players=[hero.id, ally.id])
    state.map = game_map

    # Set icons
    game_map.icons[hero.id] = hero.icon
    game_map.icons[ally.id] = ally.icon
    game_map.icons[goblin.id] = goblin.icon
    game_map.icons[orc.id] = orc.icon

    # Set positions
    hero.pos = game_map.characters[hero.id]
    ally.pos = game_map.characters[ally.id]
    orc.pos = game_map.characters[orc.id]
    goblin.pos = game_map.characters[goblin.id]

    state.characters = {hero.id: hero, ally.id: ally, orc.id: orc, goblin.id: goblin}
    state.parties = {party_players.id: party_players, party_enemies.id: party_enemies}

    graph = build_graph(config=config.agent)

    graph.invoke(state, RunnableConfig(recursion_limit=MAX_ITER))


if __name__ == "__main__":
    main()
