# Quick Start: Creating Custom Abilities

This guide shows you how to create new abilities using the composable action system.

## TL;DR

1. Create a JSON file in `agent/actions/definitions/`
2. Choose a **resolution strategy** (how to determine success)
3. Add **effects** (what happens)
4. Add **resources** (what it costs)
5. Load and test!

---

## The Recipe

Every ability has 3 ingredients:

```json
{
  "id": "my_ability",
  "name": "My Ability",
  "description": "What it does",
  "type": "attack",
  "category": "standard",
  "targeting": "single",
  "range": 5,
  
  "resolution": { /* How to determine success */ },
  "effects": [ /* What happens on success */ ],
  "resources": [ /* What it costs */ ]
}
```

---

## Step 1: Choose Resolution Strategy

### Attack Roll (d20 + mods vs AC)
**Use for**: Weapon attacks, attack spells (Fire Bolt, Eldritch Blast)

```json
"resolution": {
  "type": "attack_roll",
  "ability": "strength",        // or "dexterity", "intelligence", etc.
  "weapon_type": "martial_melee" // or "simple_ranged", "magic"
}
```

### Saving Throw (target rolls save vs DC)
**Use for**: Area spells (Fireball), status spells (Hold Person)

```json
"resolution": {
  "type": "saving_throw",
  "ability": "dexterity",       // Which save: DEX, CON, WIS, etc.
  "use_spell_dc": true          // true = spell DC, false = ability DC
}
```

### Auto Success (no roll)
**Use for**: Healing, buffs, utility

```json
"resolution": {
  "type": "auto_success"
}
```

---

## Step 2: Add Effects

### Damage
```json
"effects": [
  {
    "type": "damage",
    "damage_dice": "2d6",
    "damage_type": "fire",         // or "slashing", "cold", "necrotic", etc.
    "ability": "strength",         // optional: adds ability mod to damage
    "half_on_save": false          // optional: half damage on successful save
  }
]
```

**Damage Types**:
- Physical: `slashing`, `piercing`, `bludgeoning`
- Elements: `fire`, `cold`, `lightning`, `poison`
- Magic: `force`, `radiant`, `necrotic`, `psychic`

**Level-based scaling**: Use template variables (e.g., `"1d6+{level}"` for cantrips that scale)

### Healing
```json
"effects": [
  {
    "type": "healing",
    "heal_dice": "2d8",
    "ability": "wisdom"            // optional: adds ability mod to healing
  }
]
```

**Level-based scaling**: Use template variables in dice expressions:
```json
"effects": [
  {
    "type": "healing",
    "heal_dice": "1d10+{level}",   // Heals 1d10 + character level
    "ability": null                // null = no spellcasting modifier
  }
]
```

### Apply Status Effects
```json
"effects": [
  {
    "type": "apply_conditions",
    "conditions": [
      {
        "type": "blessed",         // See StatusType enum for options
        "duration": 10,            // turns
        "save_dc": 12,             // optional
        "traits": []               // trait modifiers
      }
    ]
  }
]
```

### Remove Status Effects
```json
"effects": [
  {
    "type": "remove_conditions",
    "condition_types": ["poisoned", "paralyzed"]  // Try in order
  }
]
```

### Multiple Effects
You can combine effects!

```json
"effects": [
  {"type": "healing", "heal_dice": "2d8"},
  {"type": "remove_conditions", "condition_types": ["poisoned"]}
]
```

---

## Step 3: Add Resources

### Action Economy
**Always required** - what action type it uses

```json
"resources": [
  {
    "type": "action_economy",
    "category": "standard",        // or "bonus", "reaction"
    "action_type": "attack",       // or "cast_spell", "special"
    "breaks_stealth": true         // optional, default true
  }
]
```

### Spell Slot
**For spells** - costs a spell slot

```json
"resources": [
  {"type": "action_economy", "category": "standard"},
  {
    "type": "spell_slot",
    "level": 1                     // 0 = cantrip (free), 1-9 = spell level
  }
]
```

### Limited Uses
**For class features** - can only use X times per rest

```json
"resources": [
  {"type": "action_economy", "category": "bonus"},
  {
    "type": "limited_uses",
    "resource_name": "rage"        // must match character resource name
  }
]
```

---

## Complete Examples

### Example 1: Greataxe Attack

A powerful two-handed weapon attack.

```json
{
  "id": "greataxe_attack",
  "name": "Greataxe Attack",
  "description": "Swing a massive greataxe",
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
      "damage_dice": "1d12",
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

### Example 2: Fireball

Area-of-effect damage spell with saving throw.

```json
{
  "id": "fireball",
  "name": "Fireball",
  "description": "A bright streak flashes to a point you choose and explodes in a roaring flame",
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
    {"type": "action_economy", "category": "standard", "action_type": "cast_spell"},
    {"type": "spell_slot", "level": 3}
  ]
}
```

### Example 3: Second Wind

Limited-use self-healing class feature with level scaling.

```json
{
  "id": "second_wind",
  "name": "Second Wind",
  "description": "Regain hit points equal to 1d10 + your fighter level",
  "type": "special",
  "category": "bonus",
  "targeting": "self",
  "range": 0,
  
  "resolution": {
    "type": "auto_success"
  },
  
  "effects": [
    {
      "type": "healing",
      "heal_dice": "1d10+{level}",
      "ability": null
    }
  ],
  
  "resources": [
    {"type": "action_economy", "category": "bonus", "action_type": "special"},
    {"type": "limited_uses", "resource_name": "second_wind"}
  ]
}
```

### Example 4: Laser Pistol (Sci-Fi)

Custom weapon for sci-fi campaign - same mechanics, different flavor!

```json
{
  "id": "laser_pistol",
  "name": "Laser Pistol",
  "description": "Fire a concentrated energy beam",
  "type": "attack",
  "category": "standard",
  "targeting": "single",
  "range": 15,
  
  "resolution": {
    "type": "attack_roll",
    "ability": "dexterity",
    "weapon_type": "simple_ranged"
  },
  
  "effects": [
    {
      "type": "damage",
      "damage_dice": "1d8",
      "damage_type": "fire",
      "ability": "dexterity"
    }
  ],
  
  "resources": [
    {"type": "action_economy", "category": "standard", "action_type": "attack"}
  ],
  
  "metadata": {
    "flavor": "The weapon hums with contained plasma energy",
    "campaign": "scifi"
  }
}
```

---

## Testing Your Ability

### 1. Create the JSON file

```bash
# Create file in definitions directory
vi agent/actions/definitions/my_ability.json
```

### 2. Load and test in Python

```python
from agent.actions.loader import ActionLoader

# Load action
action = ActionLoader.from_file("agent/actions/definitions/my_ability.json")

# Check it loaded correctly
print(action.name)
print(action.resolution)
print(action.effects)
```

### 3. Test in combat

```python
from agent.models.context import CombatContext

# Create characters and context
ctx = CombatContext()

# Execute action
action.execute(actor, target, ctx)

# Check results
if ctx.is_hit:
    print(f"Hit! Dealt {ctx.damage.total} damage")

# Finalize (consume resources)
action.finalize(actor)
```

### 4. Write a test

```python
def test_my_ability(fighter, orc):
    """Test my custom ability."""
    action = ActionLoader.from_file("agent/actions/definitions/my_ability.json")
    
    ctx = CombatContext()
    action.execute(fighter, orc, ctx)
    
    assert ctx.attack_roll is not None
    if ctx.is_hit:
        assert orc.attributes.hp < orc.max_hp
```

---

## Common Patterns

### Melee Weapon
```json
{
  "resolution": {"type": "attack_roll", "ability": "strength", "weapon_type": "martial_melee"},
  "effects": [{"type": "damage", "damage_dice": "1d8", "damage_type": "slashing", "ability": "strength"}],
  "resources": [{"type": "action_economy", "category": "standard", "action_type": "attack"}]
}
```

### Ranged Weapon
```json
{
  "resolution": {"type": "attack_roll", "ability": "dexterity", "weapon_type": "simple_ranged"},
  "effects": [{"type": "damage", "damage_dice": "1d6", "damage_type": "piercing", "ability": "dexterity"}],
  "resources": [{"type": "action_economy", "category": "standard", "action_type": "attack"}]
}
```

### Cantrip (Free Spell)
```json
{
  "resolution": {"type": "attack_roll", "ability": "intelligence", "weapon_type": "magic"},
  "effects": [{"type": "damage", "damage_dice": "1d10", "damage_type": "fire"}],
  "resources": [
    {"type": "action_economy", "category": "standard", "action_type": "cast_spell"},
    {"type": "spell_slot", "level": 0}
  ]
}
```

### AOE Save Spell
```json
{
  "resolution": {"type": "saving_throw", "ability": "dexterity"},
  "effects": [{"type": "damage", "damage_dice": "8d6", "damage_type": "fire", "half_on_save": true}],
  "resources": [
    {"type": "action_economy", "category": "standard", "action_type": "cast_spell"},
    {"type": "spell_slot", "level": 3}
  ]
}
```

### Buff Spell
```json
{
  "resolution": {"type": "auto_success"},
  "effects": [{"type": "apply_conditions", "conditions": [...]}],
  "resources": [
    {"type": "action_economy", "category": "standard"},
    {"type": "spell_slot", "level": 1}
  ]
}
```

### Healing Spell
```json
{
  "resolution": {"type": "auto_success"},
  "effects": [{"type": "healing", "heal_dice": "1d8", "ability": "wisdom"}],
  "resources": [
    {"type": "action_economy", "category": "standard"},
    {"type": "spell_slot", "level": 1}
  ]
}
```

---

## Tips & Best Practices

### 1. Name Your IDs Consistently
- Use snake_case: `fire_bolt`, `second_wind`
- Be descriptive: `longsword_attack` not `attack1`

### 2. Set Reasonable Ranges
- Melee: 1.5 meters
- Thrown: 6-10 meters
- Ranged weapons: 15-30 meters
- Spells: 6-30 meters

### 3. Balance Damage by Level
- Cantrip: 1d6-1d10
- Level 1: 2d6-3d6
- Level 2: 4d6
- Level 3: 8d6

### 4. Use Appropriate Damage Types
- **Weapons**: slashing, piercing, bludgeoning
- **Fire spells**: fire
- **Ice spells**: cold
- **Lightning**: lightning
- **Holy**: radiant
- **Unholy**: necrotic
- **Energy**: force

### 5. Test Thoroughly
- Does it load without errors?
- Does it execute in combat?
- Is the damage reasonable?
- Are resources consumed correctly?

---

## Troubleshooting

### Error: "Cannot import name..."
Make sure you import from the correct module:
```python
from agent.actions.loader import ActionLoader
```

### Error: "Invalid damage type"
Check the `DamageType` enum in `agent/models/damage.py` for valid types.

### Error: "Invalid ability"
Check the `AbilityType` enum for valid abilities: `strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`.

### Action doesn't show up
Did you load it into the registry?
```python
ActionRegistry.load_directory("agent/actions/definitions/")
```

---

## Next Steps

1. **Convert existing abilities**: Migrate Magic Missile, Bless, etc. to JSON
2. **Add more primitives**: Concentration effects, evocations, multi-target
3. **DM integration**: Let AI generate abilities from natural language
4. **Balance validation**: Auto-check abilities are balanced for their level

---

## Reference

**Available Strategies**:
- `attack_roll`
- `saving_throw`
- `auto_success`

**Available Effects**:
- `damage`
- `healing`
- `apply_conditions`
- `remove_conditions`

**Available Resources**:
- `action_economy`
- `spell_slot`
- `limited_uses`

**Template Variables** (for damage_dice and heal_dice):
- `{level}` - Character level (e.g., `"1d10+{level}"` for Second Wind)
- `{proficiency_bonus}` - Proficiency bonus (e.g., `"1d8+{proficiency_bonus}"`)

**Damage Types**: `slashing`, `piercing`, `bludgeoning`, `fire`, `cold`, `lightning`, `poison`, `necrotic`, `radiant`, `force`, `psychic`

**Abilities**: `strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`

**Action Categories**: `standard`, `bonus`, `reaction`, `movement`

**Targeting Types**: `single`, `area`, `self`, `multi`, `allies`

---

## Questions?

See also:
- `COMPOSABLE_ACTIONS_SUMMARY.md` - Full system documentation
- `REFACTOR_COMPOSABLE_ACTIONS.md` - Technical design
- `agent/actions/definitions/` - Example abilities

Happy ability creation! 🎲
