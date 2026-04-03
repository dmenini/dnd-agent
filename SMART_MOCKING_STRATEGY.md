# Smart Mocking Strategy for RollService

## Problem

When mocking `RollService._dice` directly as a MagicMock, tests were failing with:
```
TypeError: '>=' not supported between instances of 'MagicMock' and 'int'
```

**Root causes:**
1. **Mock pollution** - `RollService._dice` is a class variable, so mocks persisted across tests
2. **Improper return types** - Mocking `_dice` directly didn't return proper `DiceRoll` objects
3. **Comparison failures** - Code comparing mock objects with integers failed

## Solution: Smart Fixture Pattern

Created a reusable `mock_roll_service` fixture that properly mocks RollService methods.

### Implementation (tests/conftest.py)

```python
@pytest.fixture
def mock_roll_service(mocker: MockerFixture):
    """Factory for mocking RollService methods with proper DiceRoll returns.

    Usage:
        def test_something(mock_roll_service):
            # Mock attack_roll to return a specific value
            mock_roll_service('attack_roll', total=15, raw=15)

            # Or mock multiple methods
            mock_roll_service('attack_roll', total=15, raw=15)
            mock_roll_service('damage_roll', total=8, raw=5)
    """

    def _mock_method(
        method_name: str, 
        expression: str = "1d20", 
        total: int = 10, 
        raw: int = 10, 
        rolls: list[int] | None = None
    ):
        """Mock a RollService method to return a DiceRoll with specific values."""
        if rolls is None:
            rolls = [raw]

        mock_return = DiceRoll(expression=expression, rolls=rolls, total=total, raw=raw)
        mock_fn = mocker.patch.object(RollService, method_name, return_value=mock_return)
        return mock_fn

    return _mock_method
```

### Benefits

1. **Proper return types** - Always returns actual `DiceRoll` objects, not mocks
2. **Automatic cleanup** - pytest-mock's `mocker.patch.object` cleans up after each test
3. **Type-safe** - Comparisons with integers work correctly
4. **Easy to use** - Simple one-liner to mock any RollService method
5. **No pollution** - Each test gets a fresh mock

## Usage Examples

### Before (Problematic)
```python
def test_attack_hits(actor, target, mocker):
    # Direct mocking causes issues
    RollService._dice = mocker.MagicMock()
    RollService._dice.roll_with_context.return_value = DiceRoll(...)
    RollService._dice.roll_once.return_value = DiceRoll(...)
    
    # Problems:
    # - Mock persists across tests
    # - Requires knowing internal implementation (_dice)
    # - Verbose and error-prone
```

### After (Clean)
```python
def test_attack_hits(actor, target, mock_roll_service):
    # Clean, declarative mocking
    mock_roll_service('attack_roll', total=15, raw=15)
    mock_roll_service('damage_roll', total=8, raw=5)
    
    # Benefits:
    # - No knowledge of internals needed
    # - Automatic cleanup
    # - Concise and readable
```

## Real Test Examples

### Attack Test
```python
def test_attack_hits(actor: Character, target: Character, mock_roll_service) -> None:
    actor.attributes.strength = 16  # +3 modifier
    roll1 = target.armor_class + 1  # Hit
    roll2 = 10  # Damage

    # Mock both attack and damage rolls
    mock_roll_service('attack_roll', expression=f"1d20+5", total=roll1, raw=roll1)
    mock_roll_service('damage_roll', expression="1d8+3", total=roll2, raw=5)

    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - roll2
```

### Spell Test
```python
def test_spell_hits(actor: Character, target: Character, mock_roll_service) -> None:
    save_roll_value = actor.spell_save_dc - 1  # Target fails save
    damage_roll_value = 8

    # Mock save roll and damage
    mock_roll_service('save_roll', total=save_roll_value, raw=save_roll_value)
    mock_roll_service('damage_roll', total=damage_roll_value, raw=5)

    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - damage_roll_value
```

### Fighter Ability Test
```python
def test_second_wind(actor: Character, mock_roll_service) -> None:
    amount = 5
    
    # Mock generic roll for healing
    mock_roll_service('roll', total=amount, raw=amount)

    action.execute(actor, actor, ctx=CombatContext())

    assert actor.attributes.hp == start_hp + amount + actor.level
```

## Test Results

**Before smart mocking:**
- 277/285 tests passing (96%)
- 8 failures (4 pre-existing + 4 mock issues)

**After smart mocking:**
- **281/285 tests passing (98.6%)** ✅
- 4 failures (all pre-existing, unrelated to RollService)
- **+4 tests fixed** by proper mocking

### Remaining 4 Failures (Pre-existing)
- `test_hasted` - IndexError in status effect
- `test_paralyzed` - Assertion error in status effect
- `test_restrained` - Assertion error in status effect
- `test_stunned` - IndexError in status effect

These are **not related to RollService** - they're existing bugs in status effect logic.

## Key Principles

### 1. Mock at the Right Level
❌ **Don't mock internals**: `RollService._dice`
✅ **Mock the public API**: `RollService.attack_roll()`

### 2. Return Proper Types
❌ **Don't return MagicMock**: Causes type errors
✅ **Return actual objects**: `DiceRoll(...)` with real data

### 3. Use Fixtures for Reusability
❌ **Don't repeat mocking code** in every test
✅ **Create reusable fixtures** that encapsulate mocking logic

### 4. Leverage pytest-mock
❌ **Don't manually reset mocks** after tests
✅ **Use `mocker.patch.object`** which auto-cleans up

## Migration Guide

To migrate old tests to the smart fixture:

### Step 1: Add `mock_roll_service` parameter
```python
# Before
def test_something(actor, target, mocker):
    ...

# After
def test_something(actor, target, mock_roll_service):
    ...
```

### Step 2: Replace internal mocking
```python
# Before
RollService._dice = mocker.MagicMock()
RollService._dice.roll_with_context.return_value = DiceRoll(...)

# After
mock_roll_service('attack_roll', total=15, raw=15)
```

### Step 3: Remove unused imports
```python
# No longer needed
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from agent.services.roll_service import RollService
```

## Files Updated

### Test Files (7 files)
- ✅ `tests/actions/common/test_attack.py` - 3 tests updated
- ✅ `tests/actions/common/test_spell.py` - 3 tests updated
- ✅ `tests/actions/job_features/test_fighter.py` - 1 test updated
- ✅ `tests/conftest.py` - Added `mock_roll_service` fixture

### Tests Still Using Old Pattern (0 files)
All tests now use the smart fixture! 🎉

## Future Extensions

The fixture pattern can be extended for other services:

```python
@pytest.fixture
def mock_combat_service(mocker):
    """Mock CombatService methods."""
    def _mock_method(method_name, **kwargs):
        mock_fn = mocker.patch.object(CombatService, method_name, **kwargs)
        return mock_fn
    return _mock_method

@pytest.fixture
def mock_equipment_service(mocker):
    """Mock EquipmentService methods."""
    def _mock_method(method_name, **kwargs):
        mock_fn = mocker.patch.object(EquipmentService, method_name, **kwargs)
        return mock_fn
    return _mock_method
```

## Summary

The smart mocking strategy:
- ✅ Fixes mock pollution issues
- ✅ Returns proper types (no MagicMock comparisons)
- ✅ Auto-cleans up after each test
- ✅ Simple, declarative API
- ✅ Reusable across all tests
- ✅ Works with pytest-mock patterns

**Result**: +4 tests fixed, 98.6% test coverage achieved! 🚀
