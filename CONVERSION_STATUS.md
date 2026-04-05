# Action Conversion Status

## Summary

**Converted**: 11/18 actions (61%)  
**Blocked**: 7 actions need additional features

---

## ✅ Successfully Converted (11)

### Spells
1. **Magic Missile** - Auto-hit damage spell
2. **Sacred Flame** - Saving throw damage cantrip  
3. **Fire Bolt** - Attack roll damage cantrip
4. **Cure Wounds** - Touch healing spell
5. **Bless** - Buff with attack/save bonus
6. **Lesser Restoration** - Remove conditions
7. **Divine Favor** - Weapon damage bonus (concentration)
8. **Shield of Faith** - AC bonus (concentration)
9. **Magic Weapon** - Attack/damage bonus (concentration)

### Weapons
10. **Longsword Attack** - Basic melee weapon attack

### Class Features
11. **Second Wind** - Self-healing with level scaling

---

## ⏸️ Partially Convertible (2)

These can be converted but have limitations:

### 1. Rage
**Status**: Not converted  
**Issues**:
- Checks for heavy armor (needs conditional execution)
- Damage bonus varies by level (needs level-scaling)  
**Needed**: Conditional effects, level-based parameters

### 2. Divine Restoration
**Status**: Not converted  
**Issue**: Healing is `1d10 + (cleric level / 2)` - needs division support  
**Needed**: Expression evaluation with operators

---

## ❌ Blocked - Need New Features (5)

### 1. Arcane Recovery
**Class**: Wizard  
**What it does**: Recover spell slots up to half wizard level  
**Why blocked**: Requires custom effect to manipulate spell slots  
**Needed**: `RecoverSpellSlotsEffect` applicator

### 2. War Priest  
**Class**: Cleric (War Domain)  
**What it does**: Bonus weapon attack after Attack action  
**Why blocked**: Requires checking previous action type  
**Needed**: Conditional availability based on prior actions

### 3. Preserve Life
**Class**: Cleric (Life Domain)  
**What it does**: Heal multiple allies, capped at half their max HP, distribute points  
**Why blocked**: Complex multi-target logic with caps  
**Needed**: Custom multi-target healing effect with distribution logic

### 4. Spiritual Weapon
**Class**: Cleric (War Domain / Life Domain)  
**What it does**: Summon floating weapon that attacks as bonus action  
**Why blocked**: Requires evocation system (summoning entities)  
**Needed**: Evocation support in composable system

### 5. Guided Strike
**Class**: Cleric (War Domain passive)  
**What it does**: Use Channel Divinity after attack roll to add +10  
**Why blocked**: Reactive ability triggered mid-roll  
**Needed**: Reaction/trigger system

---

## Feature Gaps

### 1. Level-Based Scaling ✅ IMPLEMENTED
**Status**: ✅ Completed  
**Implementation**: Template variable support in `HealingEffect` and `DamageEffect`

**Supported variables**:
- `{level}` → actor.level
- `{proficiency_bonus}` → actor.attributes.proficiency_bonus

**Examples**:
```json
{
  "type": "healing",
  "heal_dice": "1d10+{level}",
  "ability": null
}
```

**Limitations**:
- No division/multiplication operators yet (needed for Divine Restoration: `1d10 + level/2`)
- Only simple addition/subtraction supported via dice expression parser

### 2. Conditional Execution
**Problem**: Some abilities require conditions to check  
**Examples**:
- Rage: Only works if not wearing heavy armor
- War Priest: Only works after Attack action

**Solution**: Add conditions to resolution or effects
```json
{
  "effects": [{
    "type": "apply_conditions",
    "conditions": ["enraged"],
    "when": {"not": {"actor.equipment.armor.type": "heavy"}}
  }]
}
```

### 3. Custom Resource Manipulation
**Problem**: Some abilities manipulate resources directly  
**Examples**:
- Arcane Recovery: Restore spell slots
- Preserve Life: Custom healing distribution

**Solution**: Create specialized effect applicators
- `RecoverSpellSlotsEffect`
- `DistributeHealingEffect`

### 4. Evocations/Summons
**Problem**: Abilities that create persistent entities  
**Examples**:
- Spiritual Weapon
- Find Familiar
- Summon Beast

**Solution**: Either:
- A. Skip evocations for now (handle separately)
- B. Add evocation support to composable system (complex)

**Recommendation**: Option A (skip for now)

### 5. Reactions and Triggers
**Problem**: Abilities that trigger mid-action  
**Examples**:
- Guided Strike: After attack roll, add +10
- Shield spell: When hit, gain +5 AC
- Counterspell: When enemy casts, attempt to counter

**Solution**: Add trigger/reaction system (major feature)

**Recommendation**: Handle separately from composable system

---

## Conversion Priority

### Phase 1: Complete Core Spells ✅ DONE
- ✅ All basic spells converted
- ✅ Second Wind with level scaling
- Skip: Arcane Recovery, War Priest, Preserve Life, Spiritual Weapon

### Phase 2: Add Level Scaling ✅ DONE
- ✅ Implemented template variable support: `"1d10+{level}"`
- ✅ Converted: Second Wind
- ⏸️ Blocked: Divine Restoration (needs division operator: `level/2`)

### Phase 3: Add Conditional Execution
- Implement condition checks in effects
- Convert: Rage (with heavy armor check)
- Convert: War Priest (with action check)

### Phase 4: Custom Effects
- Implement `RecoverSpellSlotsEffect`  
- Convert: Arcane Recovery
- Implement `DistributeHealingEffect`
- Convert: Preserve Life

### Phase 5: Advanced Features (Future)
- Evocations (Spiritual Weapon)
- Reactions (Guided Strike, Shield, Counterspell)
- Concentration management
- Multi-turn effects

---

## Current State

**Converted Actions**: Working and tested (11 actions)  
**Registration**: ✅ Updated to load from JSON  
**Level Scaling**: ✅ Implemented with template variables  
**Next Step**: Add conditional execution or custom effects

**Progress**: 11/18 core actions converted (61%)

---

## Notes

- All converted actions are fully functional
- Missing features are documented with workarounds
- Can extend system incrementally without breaking existing functionality
- Some abilities may remain Python-based for complex logic (acceptable)
