import math

from agent.character.character import Character
from agent.effects.trait_effects.support import life_steal_effect, regeneration_effect
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent, DamageType


def test_life_steal_effect_heals_actor(actor: Character, context: CombatContext) -> None:
    context.damage = Damage(components=[DamageComponent(value=10, type=DamageType.SLASHING)])
    start = 1
    actor.attributes.hp = start

    ratio = 0.2
    expected_heal = math.ceil(context.damage.total * ratio)

    life_steal_effect(actor, context, ratio)
    assert actor.attributes.hp == start + expected_heal


def test_life_steal_effect_does_nothing_without_damage(actor: Character, context: CombatContext) -> None:
    context.damage = None
    start = 1
    actor.attributes.hp = start

    life_steal_effect(actor, context, 0.5)

    assert actor.attributes.hp == start


def test_regeneration_effect_heals_actor(actor: Character) -> None:
    start = 1
    actor.attributes.hp = start

    value = 2
    regeneration_effect(actor, value)

    assert actor.attributes.hp == start + value
