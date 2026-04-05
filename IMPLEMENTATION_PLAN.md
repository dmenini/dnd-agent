# Dynamic Abilities Implementation Plan
**Concrete Implementation Guide with Code**

This document provides a step-by-step implementation plan with actual code examples, building on the high-level roadmap in `ROADMAP_DYNAMIC_ABILITIES.md`.

---

## Quick Start: 3-Week MVP

### Week 1: Foundation (Schema + Validation)
- **Days 1-2**: Define `AbilityDefinition` schema
- **Days 3-4**: Build validator with balance rules
- **Day 5**: Test with 3 example abilities

### Week 2: Loader + Integration
- **Days 1-3**: Implement `AbilityLoader` factory
- **Days 4-5**: Integrate with action registry

### Week 3: DM Tools + Testing
- **Days 1-2**: Create DM generation tools
- **Days 3-4**: End-to-end testing
- **Day 5**: Documentation and examples

---

## Phase 1: Schema Implementation

### Step 1.1: Create Schema Module

**File**: `agent/abilities/__init__.py`
```python
"""Dynamic ability system for data-driven ability creation."""
```

**File**: `agent/abilities/schema.py`
```python
from __future__ import annotations

from enum import Enum
from typing import Literal, Any
from pydantic import BaseModel, Field, field_validator

from agent.actions.base import ActionCategory, ActionType
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.models.enums import TargetingType
from agent.models.damage import DamageType


class AbilityTemplate(str, Enum):
    """High-level ability patterns"""
    WEAPON_ATTACK = "weapon_attack"
    DAMAGE_SPELL = "damage_spell"
    BUFF_SPELL = "buff_spell"
    DEBUFF_SPELL = "debuff_spell"
    HEALING_SPELL = "healing_spell"
    SUMMONING_SPELL = "summoning_spell"
    UTILITY = "utility"


class ResourceCost(BaseModel):
    """What the ability consumes"""
    action_category: ActionCategory
    spell_level: SpellLevel | None = None
    uses_per_rest: int | None = None
    requires_concentration: bool = False


class DamageSpec(BaseModel):
    """Damage dealing specification"""
    dice: str
    damage_type: DamageType
    ability_modifier: AbilityType | None = None
    
    @field_validator("dice")
    @classmethod
    def validate_dice(cls, v: str) -> str:
        """Ensure dice expression is valid"""
        import re
        if not re.match(r"^\d+d\d+(?:[+\-]\d+)?$", v):
            raise ValueError(f"Invalid dice expression: {v}")
        return v


class ConditionSpec(BaseModel):
    """Status effect to apply"""
    type: str
    duration: int
    save_dc: int = 12
    save_ability: AbilityType = AbilityType.CON
    save_mode: Literal["none", "start", "end"] = "none"
    traits: list[dict[str, Any]] = Field(default_factory=list)


class TraitSpec(BaseModel):
    """Effect modifier specification"""
    feature_id: str
    event_type: str
    params: dict[str, Any] = Field(default_factory=dict)


class AbilityDefinition(BaseModel):
    """Complete ability specification - can be stored as JSON"""
    
    # Identity
    id: str
    name: str
    description: str
    template: AbilityTemplate
    
    # Cost & Targeting
    cost: ResourceCost
    targeting: TargetingType
    range: float
    hits: int = 1
    
    # Template-specific fields
    damage: DamageSpec | None = None
    healing_dice: str | None = None
    apply_conditions: list[ConditionSpec] = Field(default_factory=list)
    remove_conditions: list[str] = Field(default_factory=list)
    
    # Attack mechanics
    requires_save: bool = False
    save_ability: AbilityType = AbilityType.DEX
    ability_modifier: AbilityType | None = None
    weapon_type: str = "magic"
    
    # Metadata
    level_required: int = 1
    tags: list[str] = Field(default_factory=list)
    flavor_text: str = ""
    
    def model_post_init(self, __context: Any) -> None:
        """Validate template-specific requirements"""
        if self.template in [AbilityTemplate.WEAPON_ATTACK, AbilityTemplate.DAMAGE_SPELL]:
            if not self.damage:
                raise ValueError(f"{self.template} requires damage specification")
        
        if self.template == AbilityTemplate.HEALING_SPELL:
            if not self.healing_dice:
                raise ValueError("Healing spells require healing_dice")
```

### Step 1.2: Create Example Definitions

**File**: `agent/abilities/examples/fire_bolt.json`
```json
{
  "id": "fire_bolt",
  "name": "Fire Bolt",
  "description": "Hurl a mote of fire at a creature or object within range",
  "template": "damage_spell",
  "cost": {
    "action_category": "standard",
    "spell_level": 0
  },
  "targeting": "single",
  "range": 24,
  "damage": {
    "dice": "1d10",
    "damage_type": "fire",
    "ability_modifier": "intelligence"
  },
  "requires_save": false,
  "weapon_type": "magic",
  "level_required": 1,
  "tags": ["fire", "ranged", "cantrip"]
}
```

**File**: `agent/abilities/examples/laser_pistol.json` (Sci-fi reskin)
```json
{
  "id": "laser_pistol",
  "name": "Laser Pistol",
  "description": "Fire a concentrated energy beam at a target",
  "template": "weapon_attack",
  "cost": {
    "action_category": "standard"
  },
  "targeting": "single",
  "range": 15,
  "damage": {
    "dice": "1d8",
    "damage_type": "fire",
    "ability_modifier": "dexterity"
  },
  "requires_save": false,
  "weapon_type": "simple_ranged",
  "level_required": 1,
  "tags": ["scifi", "energy", "ranged"],
  "flavor_text": "The plasma bolt streaks through the air with a high-pitched whine"
}
```

---

## Phase 2: Validator Implementation

### Step 2.1: Balance Rules

**File**: `agent/abilities/balance.py`
```python
from dataclasses import dataclass
import re
from agent.abilities.schema import AbilityDefinition, AbilityTemplate
from agent.character.resources import SpellLevel


@dataclass
class BalanceGuideline:
    """D&D 5e balance guidelines"""
    
    # Average damage by spell level
    SPELL_DAMAGE: dict[int, tuple[float, float]] = {
        0: (5.5, 11.0),    # Cantrip: 1d10 avg
        1: (10.5, 21.0),   # Level 1: 2d6-4d6 avg
        2: (14.0, 28.0),   # Level 2: 4d6-8d6 avg
        3: (21.0, 42.0),   # Level 3: 6d6-12d6 avg
    }
    
    # Max uses per rest by action type
    MAX_USES_PER_REST: dict[str, int] = {
        "standard": 3,  # Powerful standard action abilities
        "bonus": 5,     # Bonus actions can be more frequent
    }


class DiceCalculator:
    """Parse and evaluate dice expressions"""
    
    @staticmethod
    def average_value(dice_expr: str) -> float:
        """Calculate average value of dice expression"""
        match = re.match(r"(\d+)d(\d+)(?:([+\-])(\d+))?", dice_expr)
        if not match:
            return 0.0
        
        num, die, op, bonus = match.groups()
        num, die = int(num), int(die)
        avg = num * (die + 1) / 2
        
        if op and bonus:
            bonus_val = int(bonus)
            avg = avg + bonus_val if op == "+" else avg - bonus_val
        
        return avg


class AbilityValidator:
    """Validates abilities against D&D 5e balance"""
    
    @staticmethod
    def validate(definition: AbilityDefinition) -> tuple[bool, list[str]]:
        """
        Validate ability definition.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Schema validation already done by Pydantic
        
        # Balance validation
        errors.extend(AbilityValidator._check_damage_balance(definition))
        errors.extend(AbilityValidator._check_action_economy(definition))
        errors.extend(AbilityValidator._check_resource_costs(definition))
        errors.extend(AbilityValidator._check_targeting(definition))
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _check_damage_balance(definition: AbilityDefinition) -> list[str]:
        """Check if damage is appropriate for level"""
        errors = []
        
        if not definition.damage:
            return errors
        
        spell_level = definition.cost.spell_level or 0
        
        # Get expected damage range
        if spell_level not in BalanceGuideline.SPELL_DAMAGE:
            return errors
        
        min_dmg, max_dmg = BalanceGuideline.SPELL_DAMAGE[spell_level]
        actual_avg = DiceCalculator.average_value(definition.damage.dice)
        
        # Multiply by hits for multi-target
        actual_total = actual_avg * definition.hits
        
        if actual_total > max_dmg:
            errors.append(
                f"Damage too high: {actual_total:.1f} avg exceeds {max_dmg} "
                f"for spell level {spell_level}"
            )
        elif actual_total < min_dmg * 0.5:
            errors.append(
                f"Damage too low: {actual_total:.1f} avg is much lower than "
                f"expected {min_dmg}-{max_dmg} for spell level {spell_level}"
            )
        
        return errors
    
    @staticmethod
    def _check_action_economy(definition: AbilityDefinition) -> list[str]:
        """Check action economy rules"""
        errors = []
        
        # Bonus action spells should be level 1 max (D&D 5e rule)
        if (definition.cost.action_category == "bonus" and 
            definition.cost.spell_level and 
            definition.cost.spell_level > 1):
            errors.append(
                "Bonus action spells above 1st level break D&D 5e action economy"
            )
        
        # Reactions must have triggers (not validated yet - future enhancement)
        
        return errors
    
    @staticmethod
    def _check_resource_costs(definition: AbilityDefinition) -> list[str]:
        """Check resource costs are reasonable"""
        errors = []
        
        if definition.cost.uses_per_rest:
            max_uses = BalanceGuideline.MAX_USES_PER_REST.get(
                definition.cost.action_category, 3
            )
            if definition.cost.uses_per_rest > max_uses:
                errors.append(
                    f"Uses per rest ({definition.cost.uses_per_rest}) exceeds "
                    f"recommended max ({max_uses}) for {definition.cost.action_category}"
                )
        
        return errors
    
    @staticmethod
    def _check_targeting(definition: AbilityDefinition) -> list[str]:
        """Check targeting is reasonable"""
        errors = []
        
        # Multi-target with high damage per hit is often overpowered
        if definition.hits > 3 and definition.damage:
            avg_per_hit = DiceCalculator.average_value(definition.damage.dice)
            if avg_per_hit > 10:
                errors.append(
                    f"High damage ({avg_per_hit:.1f}) with many hits ({definition.hits}) "
                    "may be overpowered"
                )
        
        return errors
```

### Step 2.2: Validator Tests

**File**: `tests/abilities/test_validator.py`
```python
import pytest
from agent.abilities.schema import (
    AbilityDefinition, AbilityTemplate, ResourceCost, DamageSpec
)
from agent.abilities.balance import AbilityValidator, DiceCalculator
from agent.actions.base import ActionCategory
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.models.enums import TargetingType
from agent.models.damage import DamageType


def test_dice_calculator_average():
    assert DiceCalculator.average_value("1d6") == 3.5
    assert DiceCalculator.average_value("2d6") == 7.0
    assert DiceCalculator.average_value("1d8+3") == 7.5


def test_balanced_cantrip_passes():
    definition = AbilityDefinition(
        id="test_cantrip",
        name="Test Cantrip",
        description="A balanced cantrip",
        template=AbilityTemplate.DAMAGE_SPELL,
        cost=ResourceCost(
            action_category=ActionCategory.STANDARD,
            spell_level=SpellLevel.CANTRIP
        ),
        targeting=TargetingType.SINGLE,
        range=24,
        damage=DamageSpec(
            dice="1d10",
            damage_type=DamageType.FIRE
        )
    )
    
    is_valid, errors = AbilityValidator.validate(definition)
    assert is_valid
    assert len(errors) == 0


def test_overpowered_cantrip_fails():
    definition = AbilityDefinition(
        id="op_cantrip",
        name="Overpowered Cantrip",
        description="Deals way too much damage",
        template=AbilityTemplate.DAMAGE_SPELL,
        cost=ResourceCost(
            action_category=ActionCategory.STANDARD,
            spell_level=SpellLevel.CANTRIP
        ),
        targeting=TargetingType.SINGLE,
        range=24,
        damage=DamageSpec(
            dice="10d10",  # Way too much!
            damage_type=DamageType.FIRE
        )
    )
    
    is_valid, errors = AbilityValidator.validate(definition)
    assert not is_valid
    assert any("too high" in err.lower() for err in errors)


def test_bonus_action_spell_level_check():
    definition = AbilityDefinition(
        id="invalid_bonus",
        name="Invalid Bonus Action Spell",
        description="High level bonus action spell",
        template=AbilityTemplate.DAMAGE_SPELL,
        cost=ResourceCost(
            action_category=ActionCategory.BONUS,
            spell_level=SpellLevel.LEVEL_3  # Should be max level 1
        ),
        targeting=TargetingType.SINGLE,
        range=24,
        damage=DamageSpec(
            dice="8d6",
            damage_type=DamageType.FIRE
        )
    )
    
    is_valid, errors = AbilityValidator.validate(definition)
    assert not is_valid
    assert any("action economy" in err.lower() for err in errors)
```

---

## Phase 3: Loader Implementation

### Step 3.1: Action Factory

**File**: `agent/abilities/loader.py`
```python
from typing import Any
from agent.abilities.schema import AbilityDefinition, AbilityTemplate
from agent.actions.base import Action, StandardAction, BonusAction, ActionType
from agent.actions.common.attack import MainHandAttackAction, RangedAttackAction
from agent.actions.common.spell import (
    AttackSpellAction, SupportSpellAction, HealingSpellAction
)
from agent.character.abilities import AbilityType
from agent.equipment.weapons import WeaponType
from agent.models.enums import FeatureId, TargetingType


class AbilityLoader:
    """Factory that instantiates Action objects from AbilityDefinition"""
    
    @staticmethod
    def load(definition: AbilityDefinition) -> Action:
        """
        Convert AbilityDefinition → Action instance.
        
        Raises:
            NotImplementedError: If template not yet supported
            ValueError: If definition is invalid
        """
        loader_map = {
            AbilityTemplate.WEAPON_ATTACK: AbilityLoader._load_weapon_attack,
            AbilityTemplate.DAMAGE_SPELL: AbilityLoader._load_damage_spell,
            AbilityTemplate.BUFF_SPELL: AbilityLoader._load_buff_spell,
            AbilityTemplate.HEALING_SPELL: AbilityLoader._load_healing_spell,
        }
        
        loader_func = loader_map.get(definition.template)
        if not loader_func:
            raise NotImplementedError(
                f"Template {definition.template} not yet implemented"
            )
        
        return loader_func(definition)
    
    @staticmethod
    def _load_weapon_attack(definition: AbilityDefinition) -> Action:
        """Load weapon attack action"""
        if not definition.damage:
            raise ValueError("Weapon attacks require damage specification")
        
        # Determine if melee or ranged based on range
        is_ranged = definition.range > 5
        
        base_kwargs = {
            "id": definition.id,
            "name": definition.name,
            "description": definition.description,
            "damage_dice": definition.damage.dice,
            "damage_type": definition.damage.damage_type,
            "targeting": definition.targeting,
            "range": definition.range,
            "ability": definition.damage.ability_modifier or AbilityType.STR,
            "weapon_type": WeaponType(definition.weapon_type),
        }
        
        if is_ranged:
            return RangedAttackAction(**base_kwargs)
        else:
            return MainHandAttackAction(**base_kwargs)
    
    @staticmethod
    def _load_damage_spell(definition: AbilityDefinition) -> Action:
        """Load damage spell action"""
        if not definition.damage:
            raise ValueError("Damage spells require damage specification")
        
        return AttackSpellAction(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            level=definition.cost.spell_level,
            damage_dice=definition.damage.dice,
            damage_type=definition.damage.damage_type,
            targeting=definition.targeting,
            range=definition.range,
            hits=definition.hits,
            requires_save=definition.requires_save,
            ability=definition.save_ability,
            weapon_type=WeaponType(definition.weapon_type),
        )
    
    @staticmethod
    def _load_buff_spell(definition: AbilityDefinition) -> Action:
        """Load support/buff spell action"""
        from agent.effects.status_effects.base import StatusEffect
        
        # Convert ConditionSpec → StatusEffect
        conditions = []
        for cond_spec in definition.apply_conditions:
            # Build traits from trait specs
            from agent.effects.traits import TraitBuilder
            traits = []
            for trait_spec in cond_spec.traits:
                # This is simplified - would need full trait resolution
                # For now, assume traits are pre-built
                pass
            
            condition = StatusEffect(
                type=cond_spec.type,
                duration=cond_spec.duration,
                save_dc=cond_spec.save_dc,
                save_ability=cond_spec.save_ability,
                save_mode=cond_spec.save_mode,
                traits=traits,
            )
            conditions.append(condition)
        
        return SupportSpellAction(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            level=definition.cost.spell_level,
            targeting=definition.targeting,
            ability=definition.ability_modifier or AbilityType.WIS,
            range=definition.range,
            apply_conditions=conditions,
            requires_concentration=definition.cost.requires_concentration,
        )
    
    @staticmethod
    def _load_healing_spell(definition: AbilityDefinition) -> Action:
        """Load healing spell action"""
        if not definition.healing_dice:
            raise ValueError("Healing spells require healing_dice")
        
        return HealingSpellAction(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            level=definition.cost.spell_level,
            targeting=definition.targeting,
            ability=definition.ability_modifier or AbilityType.WIS,
            range=definition.range,
            heal_dice=definition.healing_dice,
        )


class AbilityRegistry:
    """Runtime registry for custom abilities"""
    
    _custom_abilities: dict[str, AbilityDefinition] = {}
    _loaded_actions: dict[str, Action] = {}
    
    @classmethod
    def register(cls, definition: AbilityDefinition) -> None:
        """Register a custom ability definition"""
        cls._custom_abilities[definition.id] = definition
        # Clear cached action if exists
        cls._loaded_actions.pop(definition.id, None)
    
    @classmethod
    def get(cls, ability_id: str) -> Action:
        """Get action instance for ability (cached)"""
        if ability_id in cls._loaded_actions:
            return cls._loaded_actions[ability_id]
        
        definition = cls._custom_abilities.get(ability_id)
        if not definition:
            raise KeyError(f"Ability {ability_id} not registered")
        
        action = AbilityLoader.load(definition)
        cls._loaded_actions[ability_id] = action
        return action
    
    @classmethod
    def load_from_json(cls, json_path: str) -> None:
        """Load ability from JSON file"""
        import json
        with open(json_path) as f:
            data = json.load(f)
        definition = AbilityDefinition.model_validate(data)
        cls.register(definition)
    
    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered custom ability IDs"""
        return list(cls._custom_abilities.keys())
```

---

## Phase 4: Integration with Character System

### Step 4.1: Extend Character Model

**File**: `agent/character/dynamic_abilities.py`
```python
"""Dynamic ability support for characters"""
from agent.abilities.schema import AbilityDefinition
from agent.abilities.loader import AbilityRegistry, AbilityLoader
from agent.actions.base import Action


class DynamicAbilityMixin:
    """Mixin to add dynamic ability support to Character"""
    
    def __init__(self):
        self._dynamic_ability_ids: list[str] = []
    
    def add_dynamic_ability(self, definition: AbilityDefinition) -> None:
        """Grant a dynamic ability to this character"""
        AbilityRegistry.register(definition)
        self._dynamic_ability_ids.append(definition.id)
    
    def get_dynamic_actions(self) -> list[Action]:
        """Get all dynamic ability actions"""
        actions = []
        for ability_id in self._dynamic_ability_ids:
            try:
                action = AbilityRegistry.get(ability_id)
                actions.append(action)
            except KeyError:
                # Ability no longer registered
                pass
        return actions
    
    def remove_dynamic_ability(self, ability_id: str) -> bool:
        """Remove a dynamic ability"""
        if ability_id in self._dynamic_ability_ids:
            self._dynamic_ability_ids.remove(ability_id)
            return True
        return False
```

**Update**: `agent/character/character.py` (add to existing Character class)
```python
# Add to imports
from agent.character.dynamic_abilities import DynamicAbilityMixin

# Modify Character class
class Character(BaseModel, DynamicAbilityMixin):
    # ... existing fields ...
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize dynamic ability support"""
        super().model_post_init(__context)
        DynamicAbilityMixin.__init__(self)
        # ... rest of existing init
```

---

## Phase 5: DM Tools

### Step 5.1: LangChain Tools

**File**: `agent/ai/ability_tools.py`
```python
from langchain_core.tools import tool
from agent.abilities.schema import AbilityDefinition
from agent.abilities.balance import AbilityValidator
from agent.abilities.loader import AbilityRegistry
import json


@tool
def list_ability_templates() -> str:
    """
    List available ability templates and their structure.
    Use this to understand what types of abilities can be created.
    """
    templates = {
        "weapon_attack": {
            "description": "Physical attack with a weapon",
            "required_fields": ["damage", "weapon_type"],
            "example": {
                "template": "weapon_attack",
                "damage": {"dice": "1d8", "damage_type": "piercing"},
                "weapon_type": "martial_melee",
                "range": 1.5
            }
        },
        "damage_spell": {
            "description": "Spell that deals damage to targets",
            "required_fields": ["damage", "spell_level", "requires_save"],
            "example": {
                "template": "damage_spell",
                "damage": {"dice": "3d6", "damage_type": "fire"},
                "spell_level": 1,
                "requires_save": True,
                "save_ability": "dexterity"
            }
        },
        "healing_spell": {
            "description": "Spell that restores hit points",
            "required_fields": ["healing_dice", "spell_level"],
            "example": {
                "template": "healing_spell",
                "healing_dice": "1d8",
                "spell_level": 1,
                "targeting": "single",
                "range": 1.5
            }
        }
    }
    return json.dumps(templates, indent=2)


@tool
def create_custom_ability(ability_json: str) -> str:
    """
    Create a custom ability from JSON specification.
    
    Args:
        ability_json: JSON string matching AbilityDefinition schema
    
    Returns:
        JSON with {"success": bool, "ability_id": str, "errors": list}
    """
    try:
        # Parse and validate schema
        definition = AbilityDefinition.model_validate_json(ability_json)
        
        # Validate balance
        is_valid, errors = AbilityValidator.validate(definition)
        
        if not is_valid:
            return json.dumps({
                "success": False,
                "errors": errors
            })
        
        # Register ability
        AbilityRegistry.register(definition)
        
        return json.dumps({
            "success": True,
            "ability_id": definition.id,
            "errors": []
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "errors": [str(e)]
        })


@tool
def validate_ability_balance(ability_json: str) -> str:
    """
    Check if an ability is balanced without registering it.
    
    Args:
        ability_json: JSON string matching AbilityDefinition schema
    
    Returns:
        JSON with {"is_valid": bool, "errors": list, "suggestions": list}
    """
    try:
        definition = AbilityDefinition.model_validate_json(ability_json)
        is_valid, errors = AbilityValidator.validate(definition)
        
        suggestions = []
        if not is_valid:
            # Generate suggestions based on errors
            if any("too high" in err for err in errors):
                suggestions.append("Try reducing damage dice or number of targets")
            if any("action economy" in err for err in errors):
                suggestions.append("Consider making this a standard action instead")
        
        return json.dumps({
            "is_valid": is_valid,
            "errors": errors,
            "suggestions": suggestions
        })
        
    except Exception as e:
        return json.dumps({
            "is_valid": False,
            "errors": [str(e)],
            "suggestions": []
        })
```

### Step 5.2: Update DM Prompt

**Update**: `agent/config.yaml`
```yaml
prompts:
  dm_ability_creation: |-
    You can create custom abilities for this campaign using these tools:
    
    WORKFLOW:
    1. Use `list_ability_templates()` to see available templates
    2. Design ability matching campaign lore (fantasy/sci-fi/horror)
    3. Use `validate_ability_balance()` to check if it's balanced
    4. If valid, use `create_custom_ability()` to register it
    5. If invalid, adjust based on error messages and retry
    
    LORE MAPPING GUIDELINES:
    - Sci-fi: Use "fire" for lasers/plasma, "force" for energy, "lightning" for electric
    - Fantasy: Standard D&D damage types (fire, cold, radiant, necrotic)
    - Horror: Prefer necrotic, poison, psychic damage types
    
    BALANCE GUIDELINES:
    - Cantrips (level 0): 1d6-1d10 single target damage
    - Level 1 spells: 2d6-3d6 damage OR strong utility
    - Bonus actions: Should be weaker than standard actions
    - Limited-use (2-3/rest): Can be 25% stronger than spell equivalent
    
    EXAMPLES:
    
    Fantasy: "Create a divine healing spell"
    ```json
    {
      "id": "healing_prayer",
      "name": "Healing Prayer",
      "description": "Channel divine energy to heal wounds",
      "template": "healing_spell",
      "cost": {"action_category": "standard", "spell_level": 1},
      "targeting": "single",
      "range": 1.5,
      "healing_dice": "1d8",
      "level_required": 1,
      "tags": ["divine", "healing"]
    }
    ```
    
    Sci-fi: "Create a laser pistol attack"
    ```json
    {
      "id": "laser_pistol_fire",
      "name": "Laser Pistol",
      "description": "Fire a concentrated energy beam",
      "template": "weapon_attack",
      "cost": {"action_category": "standard"},
      "targeting": "single",
      "range": 15,
      "damage": {"dice": "1d8", "damage_type": "fire", "ability_modifier": "dexterity"},
      "weapon_type": "simple_ranged",
      "tags": ["scifi", "energy"]
    }
    ```
    
    Always validate before creating. If validation fails, adjust and retry.
```

---

## Phase 6: Testing Strategy

### Integration Test

**File**: `tests/abilities/test_integration.py`
```python
import pytest
import json
from agent.abilities.schema import AbilityDefinition
from agent.abilities.loader import AbilityRegistry, AbilityLoader
from agent.abilities.balance import AbilityValidator
from agent.character.character import Character
from tests.conftest import create_test_fighter


def test_load_from_json_file(tmp_path):
    """Test loading ability from JSON file"""
    # Create temp JSON file
    json_path = tmp_path / "test_ability.json"
    json_path.write_text(json.dumps({
        "id": "test_bolt",
        "name": "Test Bolt",
        "description": "Test spell",
        "template": "damage_spell",
        "cost": {"action_category": "standard", "spell_level": 0},
        "targeting": "single",
        "range": 24,
        "damage": {"dice": "1d10", "damage_type": "fire"},
        "requires_save": False,
        "weapon_type": "magic",
        "level_required": 1
    }))
    
    # Load ability
    AbilityRegistry.load_from_json(str(json_path))
    
    # Verify it's accessible
    action = AbilityRegistry.get("test_bolt")
    assert action.name == "Test Bolt"
    assert action.damage_dice == "1d10"


def test_character_uses_dynamic_ability():
    """Test character can use a custom ability in combat"""
    # Create character
    fighter = create_test_fighter()
    
    # Create custom ability
    ability_def = AbilityDefinition.model_validate({
        "id": "power_strike",
        "name": "Power Strike",
        "description": "A mighty blow",
        "template": "weapon_attack",
        "cost": {"action_category": "bonus", "uses_per_rest": 2},
        "targeting": "single",
        "range": 1.5,
        "damage": {"dice": "2d6", "damage_type": "slashing"},
        "level_required": 1
    })
    
    # Add to character
    fighter.add_dynamic_ability(ability_def)
    
    # Verify character can access it
    dynamic_actions = fighter.get_dynamic_actions()
    assert len(dynamic_actions) == 1
    assert dynamic_actions[0].name == "Power Strike"


def test_scifi_weapon_generation():
    """Test generating a sci-fi weapon ability"""
    # Simulate DM generating sci-fi weapon
    scifi_weapon = {
        "id": "plasma_rifle",
        "name": "Plasma Rifle",
        "description": "High-tech energy weapon",
        "template": "weapon_attack",
        "cost": {"action_category": "standard"},
        "targeting": "single",
        "range": 20,
        "damage": {
            "dice": "2d6",
            "damage_type": "fire",  # Maps to energy damage
            "ability_modifier": "dexterity"
        },
        "weapon_type": "martial_ranged",
        "level_required": 1,
        "tags": ["scifi", "energy", "rifle"],
        "flavor_text": "The weapon hums with contained plasma"
    }
    
    definition = AbilityDefinition.model_validate(scifi_weapon)
    is_valid, errors = AbilityValidator.validate(definition)
    
    assert is_valid, f"Validation failed: {errors}"
    
    action = AbilityLoader.load(definition)
    assert action.name == "Plasma Rifle"
    assert action.range == 20
```

---

## Quick Reference: Common Patterns

### Pattern 1: Simple Damage Spell
```json
{
  "template": "damage_spell",
  "cost": {"action_category": "standard", "spell_level": 1},
  "damage": {"dice": "3d6", "damage_type": "fire"},
  "requires_save": true,
  "save_ability": "dexterity"
}
```

### Pattern 2: Healing Ability
```json
{
  "template": "healing_spell",
  "cost": {"action_category": "standard", "spell_level": 1},
  "healing_dice": "1d8",
  "targeting": "single",
  "range": 1.5
}
```

### Pattern 3: Limited-Use Class Feature
```json
{
  "template": "weapon_attack",
  "cost": {"action_category": "bonus", "uses_per_rest": 2},
  "damage": {"dice": "1d10", "damage_type": "slashing"}
}
```

---

## Deployment Checklist

- [ ] Create `agent/abilities/` module with schema, loader, validator
- [ ] Add 3 example JSON abilities (fire_bolt, laser_pistol, healing_prayer)
- [ ] Write unit tests for validator (5+ test cases)
- [ ] Write integration test for loading from JSON
- [ ] Add DM tools to LangChain agent
- [ ] Update config.yaml with DM prompt
- [ ] Test end-to-end: DM creates → validates → character uses
- [ ] Document in CLAUDE.md
- [ ] Update README with examples

---

## Next Steps After MVP

1. **Trait Builder Integration**: Support complex status effects with traits
2. **Summoning Support**: Implement evocation template
3. **Condition Templates**: Pre-built status effects (Blessed, Hasted, etc.)
4. **Scaling Rules**: "At levels 5/11/17, add 1d6 damage"
5. **UI Integration**: Display custom abilities in character sheet
6. **Persistence**: Save/load custom abilities with campaign state
7. **Library System**: Share abilities between campaigns

---

## Estimated Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Schema + Examples | 2 days | Working AbilityDefinition with JSON examples |
| Validator | 2 days | Balance validation with tests |
| Loader | 2 days | Factory creating Action instances |
| Integration | 1 day | Characters can use dynamic abilities |
| DM Tools | 2 days | LangChain tools + prompt |
| Testing | 2 days | Integration tests + bug fixes |
| Documentation | 1 day | Update CLAUDE.md, examples |
| **Total** | **12 days** | **Production-ready MVP** |
