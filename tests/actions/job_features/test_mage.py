from math import ceil

from agent.actions.jobs.mage import ArcaneRecoveryAction
from agent.character.character import Character
from agent.character.resources import SpellLevel, SpellSlots
from agent.jobs.feature import FeatureId


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

    action = ArcaneRecoveryAction(id=FeatureId.ARCANE_RECOVERY.value, description="")

    # Execute Arcane Recovery
    action.execute(actor, actor)

    # Count total slots recovered
    recovered = sum(actor.spell_slots.slots[level] - initial_slots[level] for level in actor.spell_slots.slots)

    assert recovered == max_recovery, f"Recovered {recovered}, expected {max_recovery}"

    # Finalize action consumes the bonus use
    uses_before = action.uses_per_rest
    action.finalize(actor)
    assert action.uses_per_rest == uses_before - 1
