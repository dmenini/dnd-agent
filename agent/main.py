import logging
from logging import getLogger
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from langchain_core.runnables import RunnableConfig

from agent.character.character import MeleeWeapon, Party, RangedWeapon
from agent.character.stats import Attributes, Stats
from agent.effects.hasted import Hasted
from agent.effects.poisoned import Poisoned
from agent.effects.stunned import Stunned
from agent.graph import build_graph
from agent.models.config import Config
from agent.models.enums import DamageType, TargetingType, WeaponType
from agent.models.position import Position
from agent.models.state import Character, State
from agent.models.weapons import AttackSpell, SupportSpell

MAX_ITER = 100

log = getLogger(__name__)
logging.basicConfig(level=logging.INFO)

getLogger("botocore").setLevel(logging.INFO)


def main() -> None:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Goblins", is_player_party=False)

    sword = MeleeWeapon(
        name="Sword",
        description="Heavy sword that may stun the enemy",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.LONGSWORD,
        range=2,
        targeting=TargetingType.SINGLE,
        status_effects=[Stunned(duration=1)],
    )
    bow = RangedWeapon(
        name="Bow",
        damage_dice="1d6",
        damage_type=DamageType.PIERCING,
        weapon_type=WeaponType.LONGBOW,
        range=10,
        targeting=TargetingType.SINGLE,
    )
    dagger = MeleeWeapon(
        name="Dagger",
        description="Poisonous dagger",
        damage_dice="1d5",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.DAGGER,
        range=1,
        targeting=TargetingType.SINGLE,
        status_effects=[Poisoned(duration=3, damage=1)],
    )
    fire_ball = AttackSpell(
        name="Fire Ball",
        damage_dice="1d6",
        damage_type=DamageType.MAGIC,
        range=5,
        targeting=TargetingType.SINGLE,
    )
    haste = SupportSpell(
        name="Haste",
        description="Gain 1 extra action on the next 2 turns",
        range=1,
        targeting=TargetingType.SELF,
        status_effects=[Hasted(duration=2, save_dc=0)],
    )

    hero = Character(
        id="pc_alfred",
        name="Alfred",
        icon="⚔️",
        attributes=Attributes(base_hp=20, hp=20),
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
        stats=Stats(),
        main_hand=sword,
        ranged=bow,
        spells=[fire_ball, haste],
    )
    orc = Character(
        id="orc_1",
        name="Orc Grunt",
        icon="👹",
        pos=Position(x=4, y=2),
        party=party_enemies,
        stats=Stats(),
        main_hand=MeleeWeapon(
            name="Fist",
            damage_dice="1d3",
            damage_type=DamageType.BLUDGEONING,
            weapon_type=WeaponType.OTHER,
            range=2,
            targeting=TargetingType.SINGLE,
        ),
    )

    goblin = Character(
        id="goblin_1",
        name="Goblin Dramer",
        icon="🧌",
        pos=Position(x=8, y=4),
        party=party_enemies,
        stats=Stats(),
        main_hand=dagger,
        spells=[fire_ball],
    )
    state = State(
        characters={hero.id: hero, orc.id: orc, goblin.id: goblin},
        parties={party_players.id: party_players, party_enemies.id: party_enemies},
    )

    graph = build_graph(config=config.agent)
    print(graph.get_graph().draw_mermaid())

    graph.invoke(state, RunnableConfig(recursion_limit=100))


if __name__ == "__main__":
    main()
