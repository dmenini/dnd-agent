# Composable Action System Refactor

## Problem: Current Architecture

**Too Many Classes**: 10+ action subclasses with duplicated logic
- `MainHandAttackAction`, `RangedAttackAction`, `OffHandAttackAction`
- `AttackSpellAction`, `SupportSpellAction`, `HealingSpellAction`
- `SecondWindAction`, `RageAction`, `ArcaneRecoveryAction`, etc.

**Code Duplication**:
```python
# AttackAction._apply_damage (lines 68-98)
# AttackSpellAction._apply_damage (inherited)
# → SAME CODE IN MULTIPLE PLACES
```

**Hard to Extend**: Want to add a new ability? Create a new Python class!

---

## Solution: Composable Primitives

### Core Insight

**Every action is just:**
```
Resolution Strategy → Effect Applicator → Resource Consumer
```

Examples:
- **Weapon Attack** = `attack_roll` → `apply_damage` → `consume_action`
- **Damage Spell** = `save_throw` → `apply_damage` → `consume_action + spell_slot`
- **Healing Spell** = `auto_succeed` → `apply_healing` → `consume_action + spell_slot`
- **Buff Spell** = `auto_succeed` → `apply_conditions` → `consume_action + spell_slot`

### Architecture

```python
# Single Action class with composable steps
class Action:
    resolution: ResolutionStrategy
    effects: list[EffectApplicator]
    resources: list[ResourceConsumer]
    
    def execute(self, actor, target, ctx):
        # 1. Fire start events
        ctx.fire_events(EventType.COMBAT_START)
        
        # 2. Resolve success/failure
        success = self.resolution.resolve(actor, target, ctx)
        
        # 3. Apply effects (if successful)
        if success or self.resolution.apply_on_failure:
            for effect in self.effects:
                effect.apply(actor, target, ctx)
        
        # 4. Fire end events
        ctx.fire_events(EventType.COMBAT_END)
    
    def finalize(self, actor):
        # 5. Consume resources
        for consumer in self.resources:
            consumer.consume(actor)
```

---

## Composable Primitives

### 1. Resolution Strategies

**Interface:**
```python
class ResolutionStrategy(Protocol):
    apply_on_failure: bool = False
    
    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        """Determine if action succeeds. Returns True if effects should apply."""
        ...
```

**Implementations:**

#### AttackRollStrategy
```python
class AttackRollStrategy(BaseModel):
    """Roll d20 + modifiers vs target AC"""
    ability: AbilityType
    weapon_type: WeaponType
    
    def resolve(self, actor, target, ctx) -> bool:
        roll = RollService.attack_roll(actor, self.ability, self.weapon_type, target)
        ctx.attack_roll = roll
        ctx.is_critical = roll.raw >= actor.attributes.crit_roll()
        ctx.is_hit = ctx.is_critical or roll.total >= target.armor_class
        
        # Logging
        if ctx.is_critical:
            actor.log_event(f"CRITICAL HIT! Rolled {roll.raw}", icon=Icon.ROLL)
        else:
            actor.log_event(f"Attack roll: {roll.total} vs AC {target.armor_class}", icon=Icon.ROLL)
        
        return ctx.is_hit
```

#### SavingThrowStrategy
```python
class SavingThrowStrategy(BaseModel):
    """Target rolls save vs caster's DC"""
    ability: AbilityType  # Which save (DEX, CON, WIS, etc.)
    use_spell_dc: bool = True
    
    def resolve(self, actor, target, ctx) -> bool:
        dc = actor.spell_save_dc if self.use_spell_dc else actor.attributes.ability_dc(self.ability)
        roll = RollService.save_roll(target, self.ability, is_spell=self.use_spell_dc)
        ctx.save_roll = roll
        ctx.is_hit = roll.total < dc  # Fail save = hit
        
        # Logging
        actor.log_event(f"{self.ability.name} save: {roll.total} vs DC {dc}", icon=Icon.ROLL)
        
        return ctx.is_hit
```

#### AutoSuccessStrategy
```python
class AutoSuccessStrategy(BaseModel):
    """Always succeeds (buffs, healing, utility)"""
    
    def resolve(self, actor, target, ctx) -> bool:
        return True
```

---

### 2. Effect Applicators

**Interface:**
```python
class EffectApplicator(Protocol):
    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Apply the effect to target"""
        ...
```

**Implementations:**

#### DamageEffect
```python
class DamageEffect(BaseModel):
    """Deal damage to target"""
    damage_dice: str
    damage_type: DamageType
    ability: AbilityType | None = None
    half_on_save: bool = False
    
    def apply(self, actor, target, ctx):
        # Roll damage
        roll = RollService.damage_roll(
            actor, 
            damage_dice=self.damage_dice, 
            ability=self.ability,
            is_critical=getattr(ctx, 'is_critical', False)
        )
        
        # Half damage if save succeeded and half_on_save is True
        if self.half_on_save and not ctx.is_hit:
            roll.total = roll.total // 2
        
        # Create damage object
        ctx.damage = Damage(components=[
            DamageComponent(value=roll.total, type=self.damage_type)
        ])
        
        # Apply resistances
        ctx.damage = CombatService.modify_incoming_damage(target, ctx.damage)
        
        # Trigger damage events
        TraitService.trigger_event(actor, EventType.APPLY_DAMAGE, actor, target, ctx)
        TraitService.trigger_event(target, EventType.RECEIVE_DAMAGE, actor, target, ctx)
        
        # Apply to HP
        CombatService.apply_damage(target, ctx.damage.total)
        
        # Logging
        actor.log_event(f"Damage: {ctx.damage.total} {self.damage_type.value}", icon=Icon.DAMAGE)
```

#### HealingEffect
```python
class HealingEffect(BaseModel):
    """Restore hit points"""
    heal_dice: str
    ability: AbilityType | None = None
    
    def apply(self, actor, target, ctx):
        roll = RollService.heal_roll(actor, expr=self.heal_dice)
        
        # Trigger healing events (for Disciple of Life, etc.)
        ctx.heal_roll = roll
        TraitService.trigger_event(actor, EventType.HEAL, actor, target, ctx)
        
        # Apply healing
        heal_amount = min(ctx.heal_roll.total, target.max_hp - target.attributes.hp)
        if heal_amount > 0:
            CombatService.heal(target, heal_amount)
            actor.log_event(f"Heals {target.name} for {heal_amount} HP", icon=Icon.HEAL)
```

#### ApplyConditionsEffect
```python
class ApplyConditionsEffect(BaseModel):
    """Apply status effects to target"""
    conditions: list[StatusEffect]
    
    def apply(self, actor, target, ctx):
        for condition in self.conditions:
            EffectService.try_apply_condition(target, condition)
```

#### RemoveConditionsEffect
```python
class RemoveConditionsEffect(BaseModel):
    """Remove status effects from target"""
    condition_types: list[StatusType]
    
    def apply(self, actor, target, ctx):
        for cond_type in self.condition_types:
            if EffectService.has_condition(target, cond_type):
                EffectService.remove_condition(target, cond_type)
                actor.log_event(f"Removes {cond_type.value} from {target.name}")
                break  # Only remove first match
```

#### ConcentrationEffect
```python
class ConcentrationEffect(BaseModel):
    """Handle concentration mechanics"""
    effect_to_track: StatusEffect  # The effect being concentrated on
    
    def apply(self, actor, target, ctx):
        # Break existing concentration
        if actor.concentrating_on:
            old = actor.concentrating_on
            EffectService.remove_condition(actor, old.type)
            actor.log_event(f"Stops concentrating on {old.type.value}")
        
        # Set new concentration
        actor.concentrating_on = self.effect_to_track
```

---

### 3. Resource Consumers

**Interface:**
```python
class ResourceConsumer(Protocol):
    def consume(self, actor: Character) -> None:
        """Consume resources from actor"""
        ...
```

**Implementations:**

#### ActionEconomyConsumer
```python
class ActionEconomyConsumer(BaseModel):
    """Consume action economy (standard/bonus/reaction/movement)"""
    category: ActionCategory
    action_type: ActionType
    breaks_stealth: bool = True
    
    def consume(self, actor):
        if self.category == ActionCategory.STANDARD:
            actor.action_economy.use_standard(self.action_type)
        elif self.category == ActionCategory.BONUS:
            actor.action_economy.use_bonus(self.action_type)
        # ... etc
        
        if self.breaks_stealth and actor.is_hidden:
            VisibilityService.unhide(actor)
```

#### SpellSlotConsumer
```python
class SpellSlotConsumer(BaseModel):
    """Consume a spell slot"""
    level: SpellLevel
    
    def consume(self, actor):
        actor.spell_slots.consume(self.level)
```

#### LimitedUsesConsumer
```python
class LimitedUsesConsumer(BaseModel):
    """Consume from a limited-use resource"""
    resource_name: str  # "second_wind", "rage", etc.
    
    def consume(self, actor):
        resource = actor.resources.get(self.resource_name)
        if resource:
            resource.consume()
```

---

## Refactored Action Definition

### Data-Driven Action

```python
class Action(BaseModel):
    # Identity
    id: str
    name: str
    description: str
    
    # Metadata
    type: ActionType
    category: ActionCategory
    targeting: TargetingType
    range: float
    hits: int = 1
    
    # Composable components (THIS IS THE KEY!)
    resolution: ResolutionStrategy
    effects: list[EffectApplicator]
    resources: list[ResourceConsumer]
    
    # Execution engine
    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        # Fire start events
        TraitService.trigger_event(actor, EventType.COMBAT_START, actor, target, ctx)
        TraitService.trigger_event(target, EventType.COMBAT_START, actor, target, ctx)
        
        # Resolve
        success = self.resolution.resolve(actor, target, ctx)
        
        # Apply effects
        if success or getattr(self.resolution, 'apply_on_failure', False):
            for effect in self.effects:
                effect.apply(actor, target, ctx)
        
        # Fire end events
        TraitService.trigger_event(actor, EventType.COMBAT_END, actor, target, ctx)
        TraitService.trigger_event(target, EventType.COMBAT_END, actor, target, ctx)
    
    def finalize(self, actor: Character) -> None:
        for consumer in self.resources:
            consumer.consume(actor)
    
    def is_available(self, action_economy: ActionEconomy) -> bool:
        # Check if action economy allows this
        for consumer in self.resources:
            if isinstance(consumer, ActionEconomyConsumer):
                if consumer.category == ActionCategory.STANDARD:
                    return action_economy.can_use_standard(self.type)
                elif consumer.category == ActionCategory.BONUS:
                    return action_economy.can_use_bonus(self.type)
        return True
```

---

## Example Action Definitions

### Example 1: Weapon Attack (Longsword)

**Before** (Python class):
```python
class MainHandAttackAction(StandardAction, AttackAction):
    damage_dice: str = "1d8"
    damage_type: DamageType = DamageType.SLASHING
    ability: AbilityType = AbilityType.STR
    # ... 50+ lines of code
```

**After** (JSON data):
```json
{
  "id": "longsword_attack",
  "name": "Longsword Attack",
  "description": "Strike with longsword",
  "type": "attack",
  "category": "standard",
  "targeting": "single",
  "range": 1.5,
  "resolution": {
    "type": "attack_roll",
    "ability": "strength",
    "weapon_type": "martial_melee"
  },
  "effects": [
    {
      "type": "damage",
      "damage_dice": "1d8",
      "damage_type": "slashing",
      "ability": "strength"
    }
  ],
  "resources": [
    {
      "type": "action_economy",
      "category": "standard",
      "action_type": "attack"
    }
  ]
}
```

### Example 2: Fireball Spell

**Before** (Python class):
```python
class FireballSpellAction(AttackSpellAction):
    level: SpellLevel = SpellLevel.LEVEL_3
    damage_dice: str = "8d6"
    damage_type: DamageType = DamageType.FIRE
    requires_save: bool = True
    # ... 40+ lines
```

**After** (JSON data):
```json
{
  "id": "fireball",
  "name": "Fireball",
  "type": "cast_spell",
  "category": "standard",
  "targeting": "area",
  "range": 30,
  "hits": 8,
  "resolution": {
    "type": "saving_throw",
    "ability": "dexterity",
    "use_spell_dc": true
  },
  "effects": [
    {
      "type": "damage",
      "damage_dice": "8d6",
      "damage_type": "fire",
      "half_on_save": true
    }
  ],
  "resources": [
    {
      "type": "action_economy",
      "category": "standard",
      "action_type": "cast_spell"
    },
    {
      "type": "spell_slot",
      "level": 3
    }
  ]
}
```

### Example 3: Cure Wounds

**Before** (Python class):
```python
class CureWoundsAction(HealingSpellAction):
    heal_dice: str = "1d8"
    level: SpellLevel = SpellLevel.LEVEL_1
    # ... 30+ lines
```

**After** (JSON data):
```json
{
  "id": "cure_wounds",
  "name": "Cure Wounds",
  "type": "cast_spell",
  "category": "standard",
  "targeting": "single",
  "range": 1.5,
  "resolution": {
    "type": "auto_success"
  },
  "effects": [
    {
      "type": "healing",
      "heal_dice": "1d8",
      "ability": "wisdom"
    }
  ],
  "resources": [
    {
      "type": "action_economy",
      "category": "standard",
      "action_type": "cast_spell"
    },
    {
      "type": "spell_slot",
      "level": 1
    }
  ]
}
```

### Example 4: Bless (Buff with Concentration)

**Before** (Python class):
```python
class BlessSpellAction(SupportSpellAction):
    apply_conditions: list[StatusEffect] = [Blessed]
    requires_concentration: bool = True
    # ... 40+ lines
```

**After** (JSON data):
```json
{
  "id": "bless",
  "name": "Bless",
  "type": "cast_spell",
  "category": "standard",
  "targeting": "allies",
  "range": 30,
  "hits": 3,
  "resolution": {
    "type": "auto_success"
  },
  "effects": [
    {
      "type": "concentration",
      "effect": {
        "type": "blessed",
        "duration": 10
      }
    },
    {
      "type": "apply_conditions",
      "conditions": [
        {
          "type": "blessed",
          "duration": 10,
          "traits": [
            {
              "feature_id": "attack_roll_bonus",
              "dice_expr": "1d4"
            }
          ]
        }
      ]
    }
  ],
  "resources": [
    {
      "type": "action_economy",
      "category": "standard",
      "action_type": "cast_spell"
    },
    {
      "type": "spell_slot",
      "level": 1
    }
  ]
}
```

### Example 5: Rage (Limited Use Class Feature)

**Before** (Python class, 57 lines):
```python
class RageAction(LimitedBonusAction):
    uses_per_rest: int = 2
    # ... complex execute() logic
```

**After** (JSON data):
```json
{
  "id": "rage",
  "name": "Rage",
  "type": "special",
  "category": "bonus",
  "targeting": "self",
  "resolution": {
    "type": "auto_success"
  },
  "effects": [
    {
      "type": "apply_conditions",
      "conditions": [
        {
          "type": "enraged",
          "duration": 10,
          "traits": [
            {"feature_id": "save_advantage", "ability": "strength"},
            {"feature_id": "resistance", "damage_type": "bludgeoning"},
            {"feature_id": "resistance", "damage_type": "piercing"},
            {"feature_id": "resistance", "damage_type": "slashing"},
            {"feature_id": "melee_damage_bonus", "value": 2}
          ]
        }
      ]
    }
  ],
  "resources": [
    {
      "type": "action_economy",
      "category": "bonus",
      "action_type": "special"
    },
    {
      "type": "limited_uses",
      "resource_name": "rage",
      "max_uses": 2
    }
  ]
}
```

---

## Benefits

### 1. **Massive Code Reduction**
- **Before**: 10+ Python classes, ~1000 lines
- **After**: 1 Action class + 10 composable primitives, ~500 lines
- **Ability definitions**: JSON files (~30 lines each)

### 2. **Zero-Code Ability Creation**
DM can create abilities without touching Python:
```json
{
  "id": "laser_pistol",
  "name": "Laser Pistol",
  "resolution": {"type": "attack_roll", "ability": "dexterity"},
  "effects": [{"type": "damage", "damage_dice": "1d8", "damage_type": "fire"}],
  "resources": [{"type": "action_economy", "category": "standard"}]
}
```

### 3. **Easier Testing**
```python
def test_damage_effect():
    effect = DamageEffect(damage_dice="2d6", damage_type=DamageType.FIRE)
    # Test effect in isolation
```

### 4. **Mix & Match**
Want a healing spell that also removes poison?
```json
{
  "effects": [
    {"type": "healing", "heal_dice": "2d8"},
    {"type": "remove_conditions", "condition_types": ["poisoned"]}
  ]
}
```

### 5. **Easy Balance Adjustments**
Change damage from `3d6` → `4d6`? Edit JSON, no code changes!

---

## Migration Strategy

### Phase 1: Build Composable Infrastructure (Week 1)
1. Create `agent/actions/strategies/` module with Resolution strategies
2. Create `agent/actions/effects/` module with Effect applicators
3. Create `agent/actions/resources/` module with Resource consumers
4. Write unit tests for each primitive

### Phase 2: Refactor Action Class (Week 1)
1. Update `Action` base class to use composables
2. Keep old action classes as deprecated
3. Add factory to convert JSON → Action instances

### Phase 3: Convert Existing Actions (Week 2)
1. Convert 3-5 abilities to JSON format
2. Verify combat works identically
3. Run regression tests
4. Convert remaining abilities

### Phase 4: Remove Old Code (Week 2)
1. Delete deprecated action classes
2. Update tests to use JSON definitions
3. Update documentation

---

## Implementation Priority

### High Priority (Do First)
1. **AttackRollStrategy** - Used by all weapon attacks
2. **SavingThrowStrategy** - Used by most spells
3. **DamageEffect** - Most common effect
4. **ActionEconomyConsumer** - Used by everything

### Medium Priority
5. **HealingEffect** - Common in healing spells
6. **ApplyConditionsEffect** - Buffs/debuffs
7. **SpellSlotConsumer** - All spells

### Low Priority (Can Wait)
8. **RemoveConditionsEffect** - Rare
9. **ConcentrationEffect** - Complex but few uses
10. **LimitedUsesConsumer** - Class-specific features

---

## Code Structure

```
agent/
  actions/
    __init__.py
    base.py                 # Single Action class
    
    strategies/             # Resolution strategies
      __init__.py
      attack_roll.py
      saving_throw.py
      auto_success.py
    
    effects/                # Effect applicators
      __init__.py
      damage.py
      healing.py
      conditions.py
      concentration.py
    
    resources/              # Resource consumers
      __init__.py
      action_economy.py
      spell_slots.py
      limited_uses.py
    
    definitions/            # JSON ability definitions
      core/                 # Core D&D abilities
        fire_bolt.json
        cure_wounds.json
        bless.json
      custom/               # Campaign-specific
        laser_pistol.json
        healing_nanobots.json
    
    loader.py              # JSON → Action factory
```

---

## Next Steps

1. **Prototype one primitive**: Start with `DamageEffect`
2. **Convert one action**: Convert `Longsword Attack` to use composables
3. **Test in combat**: Verify it works identically
4. **Decide**: If prototype succeeds → full migration. If not → reassess.

**Estimated Time**: 2-3 weeks for complete migration

---

## Questions for You

1. **Scope**: Should we refactor all actions, or just create the composable system for new abilities?
2. **Backward Compatibility**: Keep old action classes during transition, or hard cutover?
3. **Validation**: Should primitives validate themselves, or rely on a central validator?
4. **Performance**: Is the overhead of composition acceptable? (Probably negligible)
5. **Testing**: Migrate tests to use JSON definitions, or test primitives directly?
