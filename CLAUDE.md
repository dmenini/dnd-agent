# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a D&D tactical combat simulator featuring AI-powered NPCs. The game uses Claude (via AWS Bedrock) to control NPCs in turn-based combat, with a Textual-based terminal UI. Players create characters, engage in story mode, and fight tactical battles on grid-based maps.

## Development Commands

### Setup
```bash
# Install dependencies using uv
make install

# Clean install (removes .venv and regenerates lock)
make clean-install
```

### Running the Application
```bash
# Export AWS credentials first
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Run the game
make run
```

### Testing
```bash
# Full CI suite (format check + lint + coverage)
make test

# Run all unit tests with coverage report
make test-coverage

# Run tests without coverage
make unit-test

# Run specific test file or test case
make unit-test TEST_TARGET=tests/path/to/test.py::test_name
```

### Code Quality
```bash
# Lint (mypy + ruff check)
make lint

# Check formatting
make test-format

# Auto-format and fix issues
make format
```

## Architecture

### Game Flow
The game orchestrates three main phases managed by `GameBackend`:
1. **Character Creation** - AI-driven conversational character builder using LangGraph
2. **Story Mode** - DM-style narrative interactions (planned)
3. **Combat** - Turn-based tactical combat with AI-controlled NPCs

### Combat System Architecture

Combat is implemented as a LangGraph state machine (`agent/ai/combat_graph.py`) with five phases per turn:

```
START → DECIDE → VERIFY → EXECUTE → END
          ↑         ↓
          └─────────┘ (retry on invalid action)
```

**Nodes** (`agent/nodes/`):
- `StartCombatNode` - Initializes turn, updates visibility, checks win conditions
- `DecisionNode` - LLM decides NPC actions; human input for player turns
- `RulesVerifierNode` - Validates action legality (range, resources, targeting)
- `ActionProcessorNode` - Executes validated actions, applies effects
- `EndCombatNode` - Cleans up turn state, advances to next actor

**State Management** (`agent/models/state.py`):
- `State` - Central Pydantic model holding all game state (characters, map, turn order, visibility, etc.)
- Passed through the entire graph and mutated by nodes
- Tracks verification results, retries, current decision, and action

### Character System

**Core Classes** (`agent/character/`):
- `Character` - Main entity with attributes, HP, position, job, equipment, effects
- `Party` - Groups characters (player party vs enemy party)
- `CharacterBuilder` - Constructs characters with proper validation

**Jobs** (`agent/jobs/`):
- Base class defines features, proficiencies, equipment, and resources
- Current implementations: `Fighter`, `Wizard`, `Cleric`, `Rogue`, `Barbarian`
- Each job defines available features (attacks, spells, class abilities)

**Attributes & Abilities** (`agent/character/`):
- Standard D&D ability scores (STR, DEX, CON, INT, WIS, CHA)
- Proficiency system for skills, saves, weapons, armor
- Modifiers computed from abilities and proficiency

### Action System

**Action Registry** (`agent/actions/registry.py`):
- Maps `FeatureId` enums to action classes
- Registered at startup in `agent/registration.py`

**Action Types** (`agent/actions/`):
- `common/` - Base actions (attacks, movement, spells, evocations)
- `jobs/` - Job-specific abilities (Rage, Second Wind, Arcane Recovery, etc.)
- All actions inherit from `Action` base class which defines execution contract

**Action Base** (`agent/actions/base.py`):
- Defines action interface: `execute()`, resource checks, targeting validation
- Handles resolution of attacks, damage, healing, and effect application

### Effects System (`agent/effects/`)

Three types of effects modify character behavior:
- **Status Effects** - Temporary conditions (Blessed, Raging, Prone, etc.)
- **Trait Effects** - Passive abilities from race/class (Darkvision, Pack Tactics)
- **Evocations** - Summoned entities (e.g., Spirit Sword for Bladesinger)

Effects use hooks to modify rolls, damage, and available actions.

### Equipment System (`agent/equipment/`)

- **Slots** - HEAD, CHEST, HANDS, FEET, MAIN_HAND, OFF_HAND
- **Equipment Types** - Weapons (melee/ranged), Armor (light/medium/heavy), Consumables
- **Inventory** - Manages equipped items and available actions from equipment

### Map & Positioning (`agent/models/`)

- `GameMap` - Grid-based tactical map with walls and line-of-sight
- `Position` - x/y coordinates with direction facing
- Manhattan distance for movement and range calculations
- Visibility system accounts for walls, stealth, and perception

### AI Integration (`agent/ai/`)

**LLM Backend** (`backend.py`):
- Uses AWS Bedrock (Claude 3.7 Sonnet by default, configurable in `config.yaml`)
- Creates LLM instances via `create_llm()` in `components.py`

**Character Creation Agent** (`ai/character_creation/`):
- Conversational agent for building characters
- Uses LangGraph tools to collect character details
- Maintains creation state for save/resume

**NPC Decision Making**:
- LLM receives character sheet, visible enemies, map state, and action history
- System prompt (`config.yaml` → `prompts.npc`) defines tactical priorities
- Outputs structured decision with action type, target, and narrative description

### UI Layer (`agent/ui/`)

Built with Textual (Python TUI framework):
- `GameUI` - Main application orchestrating panels
- `MapPanel` - Grid visualization with characters and effects
- `CharacterPanel` - Displays actor's character sheet
- `LogPanel` - Scrolling combat log
- `widgets/` - Reusable components (action modal, character sheet, etc.)

### Configuration (`agent/config.yaml`)

- LLM model selection and temperature
- System prompts for NPC, DM, and map generation
- Retry limits, history size, simulation mode
- Character creation settings

## Key Design Patterns

1. **Registry Pattern** - Actions registered by feature ID for dynamic lookup
2. **State Machine** - LangGraph manages combat flow with clear phase transitions
3. **Builder Pattern** - Character construction with validation
4. **Resolver Pattern** - `character/resolvers/` handle complex stat calculations (equipment bonuses, spell effects, etc.)
5. **Effect Hooks** - Effects can modify behavior at various points (before roll, on hit, etc.)

## Important Technical Details

- **Python 3.13** required
- **uv** for dependency management (not pip)
- Uses Pydantic v2 for all models (strict validation)
- Async/await for UI and LLM calls
- Type hints enforced via mypy (strict mode)
- Ruff for linting/formatting (120 char line length)
- State is deeply copied when needed to avoid mutation bugs

## Testing

Tests use pytest with these fixtures:
- Character and party fixtures in `tests/conftest.py`
- Mock LLM responses for AI node testing
- Snapshot testing for complex state validation

When writing tests:
- Use `pytest-mock` for mocking AWS/LLM calls
- Prefer integration tests for graph flows
- Unit test individual nodes, actions, and resolvers

## Common Gotchas

- Always register new actions in `agent/registration.py` or they won't be available
- AWS credentials must be exported before running (Bedrock requirement)
- The map coordinate system has origin at top-left, y increases downward
- LangGraph state must be JSON-serializable (no complex objects in State that aren't Pydantic)
- The combat graph uses memory checkpointing - thread_id must be consistent for turn history
- Keep commits messages short and to the point