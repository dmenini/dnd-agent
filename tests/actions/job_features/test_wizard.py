from math import ceil

from agent.actions.registry import ActionRegistry
from agent.character.character import Character
from agent.character.resources import SpellLevel, SpellSlots
from agent.models.context import CombatContext
from agent.models.enums import FeatureId


def test_arcane_recovery(actor: Character) -> None:
    actor.level = 4
    actor.spell_slots = SpellSlots(
        slots={
            SpellLevel.LEVEL_1: 0,
            SpellLevel.LEVEL_2: 1,
            SpellLevel.LEVEL_3: 0,
        },
        max_slots={
            SpellLevel.LEVEL_1: 2,
            SpellLevel.LEVEL_2: 2,
            SpellLevel.LEVEL_3: 1,
        },
    )

    # Calculate expected recovery
    max_recovery = ceil(actor.level / 2)  # 4 -> recover up to 2 slots
    initial_slots = actor.spell_slots.slots.copy()

    action = ActionRegistry.create(FeatureId.ARCANE_RECOVERY)

    # Execute Arcane Recovery
    action.execute(actor, actor, ctx=CombatContext())

    # Count total slot levels recovered (not just slots, but their level value)
    slot_levels_recovered = sum(
        (actor.spell_slots.slots[level] - initial_slots[level]) * level.value for level in actor.spell_slots.slots
    )

    assert slot_levels_recovered == max_recovery, (
        f"Recovered {slot_levels_recovered} slot levels, expected {max_recovery}"
    )

    # Finalize action consumes resources
    action.finalize(actor)
    assert action.is_available(actor.action_economy) is False
