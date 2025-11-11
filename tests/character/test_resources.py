import pytest

from agent.character.resources import CasterProgression, SpellLevel, SpellSlots


def test_get_spell_slots_level_1_progression() -> None:
    """Test level 1 spell slots at all character levels."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    expected = [2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]

    for char_level in range(1, 21):
        result = spell_slots.get_spell_slots(char_level, SpellLevel.LEVEL_1)
        assert result == expected[char_level - 1]


def test_get_spell_slots_unlock_timing() -> None:
    """Test that spell levels unlock at (2 * spell_level - 1)."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)

    expected_unlocks = {
        SpellLevel.LEVEL_1: 1,
        SpellLevel.LEVEL_2: 3,
        SpellLevel.LEVEL_3: 5,
        SpellLevel.LEVEL_4: 7,
        SpellLevel.LEVEL_5: 9,
        SpellLevel.LEVEL_6: 11,
        SpellLevel.LEVEL_7: 13,
        SpellLevel.LEVEL_8: 15,
        SpellLevel.LEVEL_9: 17,
    }

    for spell_level, unlock_level in expected_unlocks.items():
        # Should be 0 one level before unlock
        if unlock_level > 1:
            result = spell_slots.get_spell_slots(unlock_level - 1, spell_level)
            assert result == 0

        # Should be > 0 at unlock level
        result = spell_slots.get_spell_slots(unlock_level, spell_level)
        assert result > 0


def test_get_spell_slots_high_level_progressions() -> None:
    """Test specific high-level slot progressions."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)

    # Level 5 spell slots increase at level 18
    assert spell_slots.get_spell_slots(17, SpellLevel.LEVEL_5) == 2
    assert spell_slots.get_spell_slots(18, SpellLevel.LEVEL_5) == 3

    # Level 6 spell slots increase at level 19
    assert spell_slots.get_spell_slots(18, SpellLevel.LEVEL_6) == 1
    assert spell_slots.get_spell_slots(19, SpellLevel.LEVEL_6) == 2

    # Level 7 spell slots increase at level 20
    assert spell_slots.get_spell_slots(19, SpellLevel.LEVEL_7) == 1
    assert spell_slots.get_spell_slots(20, SpellLevel.LEVEL_7) == 2


def test_get_spell_slots_before_unlock() -> None:
    """Test that slots are 0 before spell level unlocks."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)

    # Level 2 spells unlock at level 3
    assert spell_slots.get_spell_slots(1, SpellLevel.LEVEL_2) == 0
    assert spell_slots.get_spell_slots(2, SpellLevel.LEVEL_2) == 0

    # Level 9 spells unlock at level 17
    assert spell_slots.get_spell_slots(16, SpellLevel.LEVEL_9) == 0


def test_recompute_none_progression() -> None:
    """Test that NONE progression results in no spell slots."""
    spell_slots = SpellSlots(progression=CasterProgression.NONE)
    spell_slots.recompute(10)

    assert spell_slots.slots == {}
    assert spell_slots.max_slots == {}


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (1, {SpellLevel.LEVEL_1: 1}),
        (3, {SpellLevel.LEVEL_2: 2}),
        (5, {SpellLevel.LEVEL_3: 2}),
        (7, {SpellLevel.LEVEL_4: 2}),
        (9, {SpellLevel.LEVEL_5: 2}),
        (11, {SpellLevel.LEVEL_5: 3}),
        (17, {SpellLevel.LEVEL_5: 4}),
    ],
)
def test_recompute_pact_progression(level: int, expected: dict) -> None:
    """Test that PACT progression is handled."""
    spell_slots = SpellSlots(progression=CasterProgression.PACT)
    spell_slots.recompute(level)

    assert spell_slots.slots == expected
    assert spell_slots.max_slots == expected


def test_recompute_full_caster_level_1() -> None:
    """Test full caster at level 1."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 2
    assert spell_slots.slots[SpellLevel.LEVEL_1] == 2
    assert SpellLevel.LEVEL_2 not in spell_slots.slots


def test_recompute_full_caster_level_20() -> None:
    """Test full caster at level 20 has all spell slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(20)

    expected = {
        SpellLevel.LEVEL_1: 4,
        SpellLevel.LEVEL_2: 3,
        SpellLevel.LEVEL_3: 3,
        SpellLevel.LEVEL_4: 3,
        SpellLevel.LEVEL_5: 3,
        SpellLevel.LEVEL_6: 2,
        SpellLevel.LEVEL_7: 2,
        SpellLevel.LEVEL_8: 1,
        SpellLevel.LEVEL_9: 1,
    }
    for spell_level, expected_count in expected.items():
        assert spell_slots.max_slots[spell_level] == expected_count
        assert spell_slots.slots[spell_level] == expected_count


def test_recompute_half_caster_progression() -> None:
    """Test half caster progression (e.g., Paladin, Ranger)."""
    spell_slots = SpellSlots(progression=CasterProgression.HALF)

    # Level 2 half-caster = level 1 full caster
    spell_slots.recompute(2)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 2

    # Level 5 half-caster = level 2 full caster (rounded down from 2.5)
    spell_slots.recompute(5)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 3

    # Level 20 half-caster = level 10 full caster
    spell_slots.recompute(20)
    assert spell_slots.max_slots[SpellLevel.LEVEL_5] == 2
    assert SpellLevel.LEVEL_6 not in spell_slots.max_slots


def test_recompute_third_caster_progression() -> None:
    """Test third caster progression (e.g., Eldritch Knight, Arcane Trickster)."""
    spell_slots = SpellSlots(progression=CasterProgression.THIRD)

    # Level 3 third-caster = level 1 full caster
    spell_slots.recompute(3)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 2

    # Level 7 third-caster = level 2 full caster (rounded down from 2.31)
    spell_slots.recompute(7)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 3

    # Level 20 third-caster = level 6 full caster (rounded down from 6.6)
    spell_slots.recompute(20)
    assert spell_slots.max_slots[SpellLevel.LEVEL_3] == 3
    assert SpellLevel.LEVEL_4 not in spell_slots.max_slots


def test_recompute_slots_and_max_slots_match() -> None:
    """Test that slots and max_slots are identical after recompute."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(10)

    assert spell_slots.slots == spell_slots.max_slots


def test_recompute_excludes_cantrips() -> None:
    """Test that cantrips are not included in the slots dictionary."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(20)

    assert SpellLevel.CANTRIP not in spell_slots.slots
    assert SpellLevel.CANTRIP not in spell_slots.max_slots


def test_recompute_level_zero_defaults_to_one() -> None:
    """Test that level 0 is treated as level 1."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(0)

    # Should compute as level 1
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 2


def test_recompute_negative_level_defaults_to_one() -> None:
    """Test that negative level defaults to level 1."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(-5)

    # Should compute as level 1
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 2


def test_has_slot_cantrips_always_available() -> None:
    """Test that cantrips are always available."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    assert spell_slots.has_slot(SpellLevel.CANTRIP) is True

    # Even with no slots computed
    empty_slots = SpellSlots(progression=CasterProgression.NONE)
    assert empty_slots.has_slot(SpellLevel.CANTRIP) is True


def test_has_slot_with_available_slots() -> None:
    """Test has_slot returns True when slots are available."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    assert spell_slots.has_slot(SpellLevel.LEVEL_1) is True
    assert spell_slots.has_slot(SpellLevel.LEVEL_2) is True
    assert spell_slots.has_slot(SpellLevel.LEVEL_3) is True


def test_has_slot_without_available_slots() -> None:
    """Test has_slot returns False when no slots remain."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    # Consume all level 1 slots
    spell_slots.slots[SpellLevel.LEVEL_1] = 0

    assert spell_slots.has_slot(SpellLevel.LEVEL_1) is False


def test_has_slot_for_unlearned_spell_level() -> None:
    """Test has_slot returns False for spell levels not yet unlocked."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    assert spell_slots.has_slot(SpellLevel.LEVEL_2) is False
    assert spell_slots.has_slot(SpellLevel.LEVEL_9) is False


def test_consume_reduces_slot_count() -> None:
    """Test that consume reduces the slot count by 1."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    initial_slots = spell_slots.slots[SpellLevel.LEVEL_1]
    spell_slots.consume(SpellLevel.LEVEL_1)

    assert spell_slots.slots[SpellLevel.LEVEL_1] == initial_slots - 1


def test_consume_cantrip_does_not_reduce_slots() -> None:
    """Test that consuming cantrips doesn't affect any slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    initial_state = spell_slots.slots.copy()
    spell_slots.consume(SpellLevel.CANTRIP)

    assert spell_slots.slots == initial_state


def test_consume_raises_error_when_no_slots() -> None:
    """Test that consume raises ValueError when no slots remain."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    # Consume all slots
    spell_slots.slots[SpellLevel.LEVEL_1] = 0

    with pytest.raises(ValueError, match="No spell slots remaining"):
        spell_slots.consume(SpellLevel.LEVEL_1)


def test_consume_raises_error_for_unlearned_spell() -> None:
    """Test that consume raises ValueError for unlearned spell levels."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    with pytest.raises(ValueError, match="No spell slots remaining"):
        spell_slots.consume(SpellLevel.LEVEL_2)


def test_consume_multiple_times() -> None:
    """Test consuming multiple spell slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    initial = spell_slots.slots[SpellLevel.LEVEL_2]

    spell_slots.consume(SpellLevel.LEVEL_2)
    spell_slots.consume(SpellLevel.LEVEL_2)

    assert spell_slots.slots[SpellLevel.LEVEL_2] == initial - 2


def test_restore_all_restores_slots_to_max() -> None:
    """Test that restore_all resets slots to max_slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    # Consume some slots
    spell_slots.consume(SpellLevel.LEVEL_1)
    spell_slots.consume(SpellLevel.LEVEL_2)
    spell_slots.consume(SpellLevel.LEVEL_3)

    spell_slots.restore_all()

    assert spell_slots.slots == spell_slots.max_slots


def test_restore_all_with_no_slots_consumed() -> None:
    """Test that restore_all works even when no slots were consumed."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(10)

    initial_state = spell_slots.slots.copy()
    spell_slots.restore_all()

    assert spell_slots.slots == initial_state


def test_restore_all_after_consuming_all_slots() -> None:
    """Test restore_all after consuming all slots of a level."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(3)

    # Consume all level 2 slots
    for _ in range(2):
        spell_slots.consume(SpellLevel.LEVEL_2)

    assert spell_slots.slots[SpellLevel.LEVEL_2] == 0

    spell_slots.restore_all()

    assert spell_slots.slots[SpellLevel.LEVEL_2] == 2


def test_str_displays_all_slots() -> None:
    """Test string representation shows all spell levels."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    result = str(spell_slots)

    assert "Lv1: 4/4" in result
    assert "Lv2: 3/3" in result
    assert "Lv3: 2/2" in result


def test_str_shows_consumed_slots() -> None:
    """Test string representation reflects consumed slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    spell_slots.consume(SpellLevel.LEVEL_1)
    spell_slots.consume(SpellLevel.LEVEL_2)

    result = str(spell_slots)

    assert "Lv1: 3/4" in result
    assert "Lv2: 2/3" in result


def test_str_with_no_slots() -> None:
    """Test string representation when no slots are available."""
    spell_slots = SpellSlots(progression=CasterProgression.NONE)

    result = str(spell_slots)

    assert result == "No spell slots"


def test_str_orders_by_spell_level() -> None:
    """Test that string representation orders spell levels correctly."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(20)

    result = str(spell_slots)

    # Check that levels appear in order
    lv1_pos = result.find("Lv1:")
    lv5_pos = result.find("Lv5:")
    lv9_pos = result.find("Lv9:")

    assert lv1_pos < lv5_pos < lv9_pos


def test_full_spell_casting_workflow() -> None:
    """Test a complete workflow of casting spells and resting."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(5)

    # Cast some spells
    spell_slots.consume(SpellLevel.LEVEL_1)
    spell_slots.consume(SpellLevel.LEVEL_2)
    spell_slots.consume(SpellLevel.LEVEL_3)

    assert spell_slots.slots[SpellLevel.LEVEL_1] == 3
    assert spell_slots.slots[SpellLevel.LEVEL_2] == 2
    assert spell_slots.slots[SpellLevel.LEVEL_3] == 1

    # Rest and restore
    spell_slots.restore_all()

    assert spell_slots.slots[SpellLevel.LEVEL_1] == 4
    assert spell_slots.slots[SpellLevel.LEVEL_2] == 3
    assert spell_slots.slots[SpellLevel.LEVEL_3] == 2


def test_level_up_preserves_progression() -> None:
    """Test that leveling up correctly updates spell slots."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)

    # Start at level 2
    spell_slots.recompute(2)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 3
    assert SpellLevel.LEVEL_2 not in spell_slots.max_slots

    # Level up to 3
    spell_slots.recompute(3)
    assert spell_slots.max_slots[SpellLevel.LEVEL_1] == 4
    assert spell_slots.max_slots[SpellLevel.LEVEL_2] == 2


def test_consume_all_slots_then_try_to_cast() -> None:
    """Test error when trying to cast with no slots remaining."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(3)

    # Consume all level 2 slots
    spell_slots.consume(SpellLevel.LEVEL_2)
    spell_slots.consume(SpellLevel.LEVEL_2)

    # Try to consume one more
    with pytest.raises(ValueError, match="No spell slots remaining for level"):
        spell_slots.consume(SpellLevel.LEVEL_2)


def test_cantrip_consumption_unlimited() -> None:
    """Test that cantrips can be cast unlimited times."""
    spell_slots = SpellSlots(progression=CasterProgression.FULL)
    spell_slots.recompute(1)

    # Cast cantrip many times
    for _ in range(100):
        spell_slots.consume(SpellLevel.CANTRIP)

    # Should still be available
    assert spell_slots.has_slot(SpellLevel.CANTRIP) is True
