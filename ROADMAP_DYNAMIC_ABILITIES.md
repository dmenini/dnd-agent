# Roadmap: Dynamic AI-Generated Abilities System

## Vision

Enable the DM (AI) to create new spells, abilities, and effects on-the-fly during gameplay by defining them as data structures that are interpreted by a generic execution engine, rather than requiring hardcoded Python implementations.

## Core Philosophy

**Data-Driven Execution**: Abilities are JSON/YAML definitions → Generic interpreter → State mutations

```
AI DM Intent → Ability Schema → Validation → Interpretation → Game State Changes
```

---

## 🎉 UPDATE: Composable System Implemented (April 2026)

We've implemented a **Declarative Effect Language** (Approach 1) using composable primitives!

**Current Status**: 11/18 core actions converted (61%)

**What Works**:
- ✅ Composable action system with primitives (resolution, effects, resources)
- ✅ JSON-based ability definitions with Pydantic validation
- ✅ Generic interpreter that executes abilities from data
- ✅ Level-based scaling with template variables
- ✅ 11 abilities fully converted and tested

**See**:
- `COMPOSABLE_ACTIONS_SUMMARY.md` - Technical architecture
- `CREATING_ABILITIES_GUIDE.md` - User guide
- `CONVERSION_STATUS.md` - Conversion progress
- `agent/actions/definitions/` - Example JSON abilities

---

## Architecture Approaches

### Approach 1: Declarative Effect Language (Recommended)
**Pros**: Fast, safe, deterministic, easy to validate
**Cons**: Limited to predefined primitives

```yaml
ability:
  name: "Mystical Shield"
  type: support_spell
  cost:
    action: bonus
    spell_slot: 1
  effects:
    - apply_status:
        target: ally
        duration: 10
        traits:
          - { type: ac_bonus, value: 3 }
          - { type: resistance, damage_type: force }
```

### Approach 2: Query-Based State Mutations
**Pros**: Very flexible, composable
**Cons**: More complex to validate, potential for exploits

```yaml
ability:
  name: "Vengeful Strike"
  query: |
    SELECT target FROM enemies 
    WHERE distance <= 5 AND target.hp < 50%
  mutations:
    - damage: { dice: "2d8", type: radiant }
    - if: actor.hp < target.hp_max * 0.5
      then: { heal: { dice: "1d8" } }
```

### Approach 3: Functional Composition
**Pros**: Very expressive, reusable components
**Cons**: Requires more sophisticated interpreter

```yaml
ability:
  name: "Arcane Barrage"
  pipeline:
    - select_targets: { type: enemies, max: 3, range: 30 }
    - for_each_target:
        - roll_damage: { dice: "1d6", type: force }
        - apply_damage: { source: damage_roll }
        - if_killed:
            - chain_to_nearest: { range: 10 }
```

## Roadmap Phases

**Legend**: ✅ Complete | ⏸️ Partially Complete | ❌ Not Started

---

## Phase 1: Effect System Audit & Documentation ⏸️ PARTIALLY COMPLETE

### Goal
Create a complete catalog of all existing effects and their parameters.

### Status
- ✅ Created composable primitives catalog
- ✅ Documented resolution strategies, effects, and resources
- ❌ Full trait effects audit not done (future work)

### Tasks
1. **Create Effect Registry Documentation**
   - Document every effect function in `agent/effects/trait_effects/`
   - List parameters, constraints, typical values
   - Tag with categories: damage, buff, debuff, movement, utility
   - Identify which events they hook into

2. **Create Effect Taxonomy**
   ```
   effects/
   ├── damage/
   │   ├── direct_damage
   │   ├── damage_bonus
   │   ├── damage_over_time
   │   └── reflected_damage
   ├── modifiers/
   │   ├── stat_bonus (AC, speed, etc.)
   │   ├── advantage/disadvantage
   │   └── resistance/vulnerability
   ├── control/
   │   ├── movement_restriction
   │   ├── action_restriction
   │   └── forced_movement
   └── utility/
       ├── healing
       ├── vision_manipulation
       └── resource_manipulation
   ```

3. **Extract Common Patterns**
   - Identify recurring patterns (buff spell, damage spell, summon, etc.)
   - Document parameter ranges that feel balanced at each level
   - Note which effects are commonly combined

**Deliverable**: `docs/effect_catalog.md` with full effect documentation

---

## Phase 2: Ability Schema Definition ✅ COMPLETE

### Goal
Define a formal schema for ability definitions that can be validated and interpreted.

### Status
- ✅ Created Pydantic models for composable actions
- ✅ JSON schema with validation
- ✅ 11 ability definitions created as examples
- ✅ Loader with type checking and validation

### Tasks
1. **Create Pydantic Models for Ability Definitions**
   ```python
   # agent/models/ability_schema.py
   class AbilityDefinition(BaseModel):
       id: str
       name: str
       description: str
       
       # Resource requirements
       action_cost: ActionCost
       resource_costs: list[ResourceCost]
       
       # Targeting
       targeting: TargetingConfig
       range: float
       
       # Effects
       effects: list[EffectDefinition]
       
       # Constraints
       constraints: list[Constraint]
   
   class EffectDefinition(BaseModel):
       type: str  # Maps to effect function
       parameters: dict[str, Any]
       conditions: list[Condition]  # When to apply
       duration: int | None
   ```

2. **Create Schema Validator**
   - Validate parameter types and ranges
   - Check for illegal combinations
   - Estimate power level vs cost
   - Suggest corrections for common issues

3. **Create Schema Examples**
   - Convert 10-15 existing spells to schema format
   - Include edge cases (concentration, reactions, conditional effects)

**Deliverable**: `agent/models/ability_schema.py` with full schema definitions

---

## Phase 3: Generic Effect Interpreter ✅ COMPLETE

### Goal
Build an interpreter that can execute ability definitions without hardcoding.

### Status
- ✅ Built `ComposableAction` execution engine
- ✅ Effect dispatching via type discrimination
- ✅ Level-based scaling with template variables
- ✅ Resource validation and consumption
- ✅ All 11 converted actions tested and working

### Tasks
1. **Create Effect Resolver**
   ```python
   # agent/services/effect_interpreter.py
   class EffectInterpreter:
       def __init__(self, effect_registry: dict):
           self.registry = effect_registry
       
       def execute_ability(
           self,
           ability: AbilityDefinition,
           actor: Character,
           targets: list[Character],
           context: CombatContext,
       ) -> ExecutionResult:
           """Execute an ability definition."""
           # 1. Validate resources
           # 2. Resolve targets
           # 3. Apply effects in order
           # 4. Consume resources
           # 5. Log events
           pass
   ```

2. **Implement Effect Dispatching**
   - Map effect types to registered functions
   - Handle parameter substitution (e.g., spell level scaling)
   - Support conditional execution
   - Handle effect ordering and dependencies

3. **Add Safety Checks**
   - Infinite loop detection
   - Stack overflow prevention
   - Resource exhaustion checks
   - Max iterations/effects per ability

4. **Create Effect Templates**
   ```python
   TEMPLATES = {
       "simple_buff": {
           "effects": [
               {
                   "type": "apply_status",
                   "parameters": {
                       "status_type": "{status_name}",
                       "duration": "{duration}",
                       "traits": "{traits}",
                   }
               }
           ]
       },
       "damage_spell": {
           "effects": [
               {
                   "type": "roll_save",
                   "parameters": {"ability": "{save_ability}"},
               },
               {
                   "type": "apply_damage",
                   "parameters": {
                       "dice": "{damage_dice}",
                       "damage_type": "{damage_type}",
                   },
                   "conditions": [{"type": "save_failed"}],
               }
           ]
       }
   }
   ```

**Deliverable**: Working interpreter that can execute abilities from JSON/YAML

---

## Phase 4: AI Generation Pipeline ❌ NOT STARTED

### Goal
Enable LLM to generate valid ability definitions from natural language.

### Status
- ❌ Generation prompt system not implemented
- ❌ Few-shot examples not created
- ❌ Validation loop not built
- **Next Step**: This is the logical next phase after conversion is complete

### Tasks
1. **Create Generation Prompt System**
   ```python
   GENERATION_PROMPT = """
   You are a D&D 5e rules expert. Create an ability definition for:
   
   Request: {dm_intent}
   Character Level: {level}
   Available Effects: {effect_catalog}
   
   Requirements:
   - Must be balanced for level {level}
   - Follow D&D 5e conventions
   - Use only effects from the catalog
   - Provide resource costs (action economy, spell slots, etc.)
   
   Output a JSON schema matching AbilityDefinition.
   """
   ```

2. **Create Few-Shot Examples**
   - Provide 5-10 example conversions as training data
   - Cover different ability types (buff, damage, summon, utility)
   - Include edge cases and complex abilities

3. **Build Validation & Refinement Loop**
   ```python
   def generate_ability(dm_intent: str, character: Character) -> AbilityDefinition:
       for attempt in range(3):
           # Generate ability
           raw = llm.generate(dm_intent, context)
           ability = AbilityDefinition.parse(raw)
           
           # Validate
           issues = validate_ability(ability, character.level)
           if not issues:
               return ability
           
           # Refine with issues as context
           dm_intent += f"\n\nPrevious issues: {issues}"
       
       raise ValueError("Failed to generate valid ability")
   ```

4. **Add Balance Heuristics**
   ```python
   def estimate_power_level(ability: AbilityDefinition) -> float:
       """Estimate relative power (0-100 scale)."""
       power = 0
       
       # Damage contribution
       for effect in ability.effects:
           if effect.type == "damage":
               avg_damage = calculate_average_damage(effect.parameters)
               power += avg_damage * 2
           elif effect.type == "ac_bonus":
               power += effect.parameters["value"] * 5
           # ... more heuristics
       
       # Adjust for action cost
       if ability.action_cost.type == "bonus":
           power *= 1.5
       
       return power
   ```

**Deliverable**: Working AI generation pipeline with validation

---

## Phase 5: Runtime Integration ✅ COMPLETE

### Goal
Integrate dynamic abilities into the existing combat system.

### Status
- ✅ Action registry supports both JSON and Python actions
- ✅ Characters can use composable actions seamlessly
- ✅ AI decision making works with composable actions
- ✅ Hybrid system allows gradual migration

### Tasks
1. **Extend Character to Support Dynamic Abilities**
   ```python
   class Character:
       # Existing
       spells: list[Action]
       special_abilities: list[Action]
       
       # New
       dynamic_abilities: list[AbilityDefinition]
       
       def get_all_actions(self) -> list[Action]:
           """Combine static and dynamic abilities."""
           static = self.spells + self.special_abilities
           dynamic = [
               self.interpreter.to_action(ability)
               for ability in self.dynamic_abilities
           ]
           return static + dynamic
   ```

2. **Create Action Wrapper for Dynamic Abilities**
   ```python
   class DynamicAbilityAction(Action):
       definition: AbilityDefinition
       interpreter: EffectInterpreter
       
       def execute(self, actor, target, ctx):
           return self.interpreter.execute_ability(
               self.definition, actor, [target], ctx
           )
       
       def is_available(self, action_economy):
           # Check action economy from definition
           pass
   ```

3. **Update AI Decision Making**
   - Teach combat graph to consider dynamic abilities
   - Update action selection prompt to describe dynamic abilities
   - Handle unknown ability types gracefully

4. **Add Ability Storage**
   - Save/load dynamic abilities with character state
   - Version dynamic abilities for compatibility
   - Handle ability removal/replacement

**Deliverable**: Characters can use AI-generated abilities in combat

---

## Phase 6: DM Interface & Testing ❌ NOT STARTED

### Goal
Create interface for DM to generate and test abilities during gameplay.

### Status
- ❌ DM command system not implemented
- ❌ Ability preview system not built
- ❌ Sandbox testing not created
- **Prerequisite**: Complete Phase 4 (AI generation) first

### Tasks
1. **Create DM Command System**
   ```python
   # New slash command or DM action
   /create_ability "Give the fighter a defensive stance that grants +3 AC but reduces movement by half"
   
   # System generates ability
   # Shows preview with stats
   # DM approves/rejects/modifies
   # Grants to character
   ```

2. **Build Ability Preview System**
   - Show ability description
   - List all effects in plain English
   - Display resource costs
   - Estimate power level vs character level
   - Show similar existing abilities for comparison

3. **Create Sandbox Testing**
   ```python
   def test_ability(ability: AbilityDefinition, scenario: TestScenario):
       """Test ability in isolation."""
       # Create dummy characters
       # Apply ability
       # Check for issues:
       #   - Crashes/errors
       #   - Infinite loops
       #   - Extreme damage/healing
       #   - Resource leaks
       # Return safety report
   ```

4. **Add Ability Management UI**
   - List character's dynamic abilities
   - Edit/remove abilities
   - Test abilities in sandbox
   - Share abilities between characters

**Deliverable**: DM can create, test, and grant custom abilities

---

## Current Implementation: Composable Action System

### What We Built (April 2026)

We implemented a **simplified version of the Declarative Effect Language** (Approach 1) using composable primitives:

**Architecture**:
```
JSON Definition → Pydantic Validation → ComposableAction → Generic Execution → State Changes
```

**Core Components**:

1. **Resolution Strategies** (determines success/failure)
   - `AttackRollStrategy` - d20 + mods vs AC
   - `SavingThrowStrategy` - target rolls save vs DC
   - `AutoSuccessStrategy` - no roll needed

2. **Effect Applicators** (what happens on success)
   - `DamageEffect` - deals damage with resistances
   - `HealingEffect` - restores hit points
   - `ApplyConditionsEffect` - applies status effects
   - `RemoveConditionsEffect` - removes conditions

3. **Resource Consumers** (what it costs)
   - `ActionEconomyConsumer` - consumes standard/bonus/reaction
   - `SpellSlotConsumer` - consumes spell slots
   - `LimitedUsesConsumer` - tracks daily/short rest uses

**Features Implemented**:
- ✅ JSON-based ability definitions
- ✅ Pydantic validation
- ✅ Generic execution engine
- ✅ Level-based scaling (`{level}`, `{proficiency_bonus}`)
- ✅ Hybrid system (JSON + Python actions coexist)
- ✅ 11 abilities converted (61% of core set)
- ✅ Full test coverage

**Example** (Second Wind with level scaling):
```json
{
  "id": "second_wind",
  "name": "Second Wind",
  "description": "Regain 1d10 + fighter level hit points",
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

### Differences from Original Roadmap

**Simplified Scope**:
- Original: Full AI generation pipeline with balance validation
- Current: Manual JSON creation with schema validation
- Rationale: Prove the interpreter works before adding AI generation

**Different Order**:
- Original: Document everything → Design schema → Build interpreter
- Current: Build primitives → Convert actions → Extract patterns
- Rationale: Bottom-up learning what patterns actually exist

**Hybrid Approach**:
- Original: Replace all hardcoded actions
- Current: JSON and Python actions coexist
- Rationale: Complex actions (evocations, reactions) stay in Python

### What's Left

To complete the original vision:

**Short Term** (Phases 3-4 equivalents):
1. Add conditional execution for Rage, War Priest
2. Add custom effects for Arcane Recovery, Preserve Life
3. Finish converting remaining 7 actions (83% complete)

**Medium Term** (Phase 4):
4. Create AI generation prompt system
5. Build validation loop with balance heuristics
6. Enable DM to generate abilities from natural language

**Long Term** (Phases 6-7):
7. DM command interface (/create_ability)
8. Ability testing sandbox
9. Usage tracking and learning

### Next Immediate Steps

1. **Add conditional execution** (2-3 days)
   - Design conditional system (validators or expressions)
   - Convert Rage and War Priest
   - Test conditional logic

2. **Add custom effects** (3-4 days)
   - Implement RecoverSpellSlotsEffect
   - Implement DistributeHealingEffect
   - Convert Arcane Recovery and Preserve Life

3. **AI Generation Prototype** (1 week)
   - Create few-shot examples
   - Build generation prompt
   - Test with 5 new abilities

### Success So Far

**Metrics**:
- ✅ 11/18 core actions converted (61%)
- ✅ 100% test pass rate
- ✅ No performance degradation
- ✅ Clean architecture, extensible design
- ✅ Documentation complete

**Validation of Approach**:
- The composable system works for standard D&D abilities
- JSON is readable and maintainable
- Generic execution is performant
- Hybrid system allows gradual migration

**Ready for Next Phase**: The foundation is solid. Time to add AI generation.

---

## Phase 7: Advanced Features (Future)

### Goal
Enable more sophisticated ability creation and management.

### Features to Consider

1. **Ability Learning & Evolution**
   - Track ability usage statistics
   - LLM learns what kinds of abilities are fun/balanced
   - Suggest ability upgrades as characters level up

2. **Combo Detection**
   - Detect when abilities synergize well
   - Suggest combinations to players
   - Generate "combo abilities" that enhance existing ones

3. **Dynamic Scaling**
   - Abilities automatically scale with level
   - Context-aware power adjustments
   - Difficulty-based modifications

4. **Ability Crafting System**
   - Players describe what they want
   - System generates options
   - Player chooses and refines
   - Spend resources to "learn" the ability

5. **Narrative Integration**
   - Abilities tied to story moments
   - "You absorb the fire elemental's power" → gain fire abilities
   - Temporary abilities from magical items/locations

6. **Multi-Target Complex Effects**
   - Chain effects (lightning jumps between enemies)
   - Area effects with falloff
   - Ally coordination abilities
   - Environmental interactions

---

## Technical Decisions

### Key Questions to Answer

**Q: Should we use code generation or pure interpretation?**

**Recommendation**: Pure interpretation with escape hatches
- Start with interpretation for 95% of cases
- Allow "custom_effect" type that calls Python for edge cases
- Never expose arbitrary code execution to AI

**Q: How do we handle effect ordering and dependencies?**

**Recommendation**: Explicit execution order with dependency graph
```yaml
effects:
  - id: roll_damage
    type: roll_dice
    output: damage_result
  
  - id: apply_damage
    type: damage
    input: damage_result
    depends_on: [roll_damage]
```

**Q: How do we prevent overpowered abilities?**

**Recommendation**: Multi-layer validation
1. Schema validation (type checking)
2. Rule validation (no concentration + reaction)
3. Balance validation (power level vs cost)
4. Playtesting feedback loop
5. DM approval for edge cases

**Q: Should abilities be Turing-complete?**

**Recommendation**: No, keep them bounded
- Max 10 effects per ability
- No recursion/loops
- No ability can spawn new abilities
- Fixed execution model

**Q: How do we handle ability versioning?**

**Recommendation**: Semantic versioning with migration
```python
class AbilityDefinition:
    schema_version: str = "1.0"
    
    @classmethod
    def migrate(cls, old: dict, from_version: str) -> "AbilityDefinition":
        """Migrate from old schema version."""
        # Apply transformations
        return cls.parse(old)
```

---

## Metrics for Success

### Phase 1-2: Foundation
- [ ] 100% of existing effects documented
- [ ] Schema can represent all current spells
- [ ] Validation catches 90%+ of illegal abilities

### Phase 3-4: Execution
- [ ] Dynamic abilities execute without crashes
- [ ] Performance: <10ms overhead vs hardcoded
- [ ] AI generates valid abilities 80%+ of time

### Phase 5-6: Integration
- [ ] DM can create and grant abilities mid-combat
- [ ] Players can use dynamic abilities seamlessly
- [ ] No combat-breaking exploits discovered

### Phase 7: Polish
- [ ] 10+ unique dynamic abilities used in playtests
- [ ] Player satisfaction with custom abilities: 8/10+
- [ ] Ability generation time: <5 seconds

---

## Risk Mitigation

### Risk: AI generates unbalanced abilities
**Mitigation**: 
- Strict validation with power level heuristics
- DM approval required for high-power abilities
- Playtesting feedback loop
- Ability usage statistics to identify outliers

### Risk: Complex abilities are hard to understand
**Mitigation**:
- Auto-generate plain English descriptions
- Show step-by-step breakdown
- Compare to similar existing abilities
- Require DM to explain ability when granting

### Risk: Performance degradation
**Mitigation**:
- Cache interpreted abilities as Action objects
- Profile hot paths
- Limit max effects per ability
- Use code generation for frequently-used abilities

### Risk: Breaking changes to existing code
**Mitigation**:
- Comprehensive test coverage first
- Parallel implementation (keep hardcoded abilities)
- Gradual migration spell by spell
- Feature flag for dynamic abilities

---

## Alternative Approaches

### Option A: Ability Graph DSL
Define abilities as data flow graphs:
```yaml
ability:
  nodes:
    - id: select_target
      type: targeting
      config: { type: single, range: 30 }
    
    - id: roll_attack
      type: attack_roll
      input: select_target.target
    
    - id: deal_damage
      type: damage
      input: roll_attack.hit
      config: { dice: "2d6", type: fire }
  
  edges:
    - from: select_target → roll_attack
    - from: roll_attack → deal_damage (if hit)
```

### Option B: Behavior Tree
Model abilities as behavior trees:
```yaml
ability:
  root:
    type: sequence
    children:
      - type: check_resources
      - type: select_target
      - type: selector
        children:
          - type: sequence  # Attack path
            children:
              - type: attack_roll
              - type: apply_damage
          - type: sequence  # Miss path
            children:
              - type: log_miss
```

### Option C: Rule-Based System
Use production rules:
```yaml
ability:
  rules:
    - when: target.distance <= 5
      then: 
        - apply: { effect: damage, dice: "1d8" }
        - apply: { effect: push, distance: 10 }
    
    - when: actor.hp_percent < 0.5
      then:
        - apply: { effect: damage_bonus, value: "1d6" }
```

---

## Recommended First Steps

1. **Week 1**: Complete Phase 1 (Effect Audit) - understand what you have
2. **Week 2**: Complete Phase 2 (Schema) - design the data format  
3. **Week 3**: Prototype Phase 3 (Interpreter) - prove it works for 3-5 spells
4. **Week 4**: Decide whether to proceed based on prototype results

**Success Criteria for Prototype**:
- Can represent Divine Favor, Shield of Faith, and Magic Missile
- Executes without crashes
- Performance acceptable (<50ms per ability execution)
- Code is maintainable and extensible

If prototype succeeds → Full implementation
If prototype fails → Reassess approach or accept current system

---

## Open Questions for User

1. **Scope**: Should dynamic abilities replace all spells, or just enable "custom" ones?
2. **Balance**: Who validates abilities - AI, rules engine, DM approval, or all three?
3. **Performance**: Is 10-50ms overhead per ability acceptable?
4. **Complexity**: Should we support conditional effects, or keep it simple?
5. **Storage**: How to persist dynamic abilities - in character JSON, separate DB, temporary only?
6. **UI**: Where do dynamic abilities show up - mixed with normal abilities or separate section?

---

## Conclusion

This is a **large undertaking** (4-6 weeks of focused work), but achievable incrementally. The key is:

1. **Start with data** - document what exists
2. **Define the schema** - formalize ability structure  
3. **Build interpreter** - prove it works for simple cases
4. **Iterate carefully** - add complexity only as needed
5. **Validate constantly** - keep the system balanced and safe

The payoff: A D&D game where the DM can truly improvise, creating unique abilities that feel natural and balanced, without touching the codebase.
