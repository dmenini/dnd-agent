import asyncio
import logging
from logging import getLogger
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from agent.ai.map_generator import build_map_generator, generate_game_map
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
from agent.models.position import Position
from agent.models.state import Character, State
from agent.registration import register_actions, register_traits
from agent.ui.game_ui import GameUI

MAX_ITER = 300
MAP_SIZE = 10

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

    player_party = Party(id="p1", name="Heroes", is_player_party=True)
    enemy_party = Party(id="p2", name="Goblins", is_player_party=False)

    state.log.log_event(
        message=f"Setting up combat simulation: {player_party.name} vs {enemy_party.name}",
        log_type=LogLevel.MAIN,
    )

    sword = MeleeWeapon(
        name="Sword",
        description="Heavy sword that may stun the enemy",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
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
        targeting=TargetingType.SINGLE,
        effects=[Poisoned(duration=3)],
    )

    heroes = [
        Character(
            id="pc_alfred",
            name="Alfred",
            icon="🤡",
            pos=Position(x=0, y=0),
            job=Fighter,
            attributes=Attributes(base_hp=20),
            is_player=True,
            party=player_party,
            main_hand=sword,
            ranged=bow,
        ),
        Character(
            id="pc_alice",
            name="Alice",
            icon="👧",
            pos=Position(x=1, y=1),
            job=Mage,
            attributes=Attributes(base_hp=20),
            is_player=True,
            party=player_party,
            main_hand=sword,
            ranged=bow,
        ),
    ]
    enemies = [
        Character(
            id="orc_1",
            name="Orc Grunt",
            icon="👹",
            pos=Position(x=2, y=2),
            job=Fighter,
            party=enemy_party,
        ),
    ]

    state.log.log_event(message=f"Generating combat map of size {MAP_SIZE}x{MAP_SIZE}", log_type=LogLevel.MAIN)

    gen = build_map_generator(config.agent)

    if config.agent.decision_node.get("mock_llm"):
        positions = {c.id: c.pos for c in heroes + enemies}
        game_map = GameMap(map="", width=MAP_SIZE, height=MAP_SIZE, walls=[], characters=positions)
    else:
        game_map = generate_game_map(
            gen,
            enemies=[c.id for c in enemies],
            players=[c.id for c in heroes],
            map_size=MAP_SIZE,
        )

    state.map = game_map

    for char in heroes + enemies:
        game_map.icons[char.id] = char.icon
        char.pos = game_map.characters[char.id]

    # Register in state
    state.characters = {c.id: c for c in heroes + enemies}
    state.parties = {player_party.id: player_party, enemy_party.id: enemy_party}

    ui = GameUI(initial_state=state, config=config)
    await ui.run_async()


if __name__ == "__main__":
    asyncio.run(main())
