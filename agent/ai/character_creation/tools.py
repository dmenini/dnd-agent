from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.builder import CharacterBuilder, CharacterSelections, options_map
from agent.jobs.base import JobType

if TYPE_CHECKING:
    from agent.ai.character_creation.agent import CharacterCreationAgent


def get_class_options(job_type: JobType) -> str:
    options = options_map.get(job_type)
    if not options:
        return f"No detailed options found for {job_type.value}"

    result = f"Options for {job_type.value}:\n\n"

    # Features
    if options.feature_options:
        result += "\n**Class Features**:\n"
        for feat_choice in options.feature_options:
            result += f"  {feat_choice.feature_name} - {feat_choice.description}:\n"
            for opt in feat_choice.options:
                result += f"    - {opt}\n"

    # Skills
    result += f"\n**Skills** (choose {options.skill_count}):\n"
    for skill in options.skill_options:
        result += f"  - {skill.value}\n"

    # Equipment
    if options.equipment_options:
        result += "\n**Equipment Choices**:\n"
        for eq_choice in options.equipment_options:
            result += f"  {eq_choice.slot.value} - {eq_choice.description}:\n"
            for opt in eq_choice.options:
                result += f"    - {opt}\n"

    return result


def save_base_character(context: CharacterCreationAgent, character: CharacterBuilder) -> str:
    context.current_builder = character
    return (
        f"Started creating {character.name}, the {character.job.value}! "
        f"As a next step, the player must choose their skills, equipment, and features. "
        f"Use get_class_options_tool to see what's available."
    )


def save_player_selections(context: CharacterCreationAgent, selections: CharacterSelections) -> str:
    if not context.current_builder:
        return "No character is currently being created. Use start_character_creation first."

    options = options_map.get(context.current_builder.job)
    if not options:
        return "Cannot set player selections - no options available for this class."

    try:
        selections.validate_skills(options.skill_options, options.skill_count)
        selections.validate_equipment_choices(options.equipment_options)
        selections.validate_feature_choices(options.feature_options)
    except ValueError as e:
        return str(e)

    context.current_builder.selections = selections
    return f"Player's selections set! Character {context.current_builder.name} can now be finalized."


def finalize_character(context: CharacterCreationAgent) -> str:
    if not context.current_builder:
        return "No character is currently being created."

    # Validate all required choices are made
    options = options_map.get(context.current_builder.job)
    if options:
        # Check skills
        if len(context.current_builder.selections.skill_proficiencies) != options.skill_count:
            return f"Must choose {options.skill_count} skills before finalizing."

        # Check equipment
        missing_equipment = [
            e.slot for e in options.equipment_options if e.slot not in context.current_builder.selections.equipment
        ]
        if missing_equipment:
            return f"Missing equipment choices: {missing_equipment}"

        # Check features
        missing_features = [
            f.feature_name
            for f in options.feature_options
            if f.feature_name not in context.current_builder.selections.features
        ]
        if missing_features:
            return f"Missing feature choices: {missing_features}"

    # Save character
    context.characters.append(context.current_builder)
    msg = f"Character creation complete: {context.current_builder.name}"

    context.current_builder = None

    if len(context.characters) == context.max_players:
        context.done = True

    return msg


def get_party_status(context: CharacterCreationAgent) -> str:
    remaining = context.max_players - len(context.characters)

    if remaining > 0:
        summary = f"Players have created {len(context.characters)}/{context.max_players} character(s)"
        for char in context.characters:
            summary += f"\n- {char.name}: {char.summary}"

        if context.current_builder:
            summary += f"\n\nCurrently creating: {context.current_builder.name}"
        else:
            summary += f"\n\nThey can create {remaining} more."

        return summary

    return f"Players have created the maximum of {context.max_players} characters! Party is complete."


def finalize_party(context: CharacterCreationAgent) -> str:
    context.done = True

    summary = f"Party complete with {len(context.characters)}/{context.max_players} character(s):\n"
    for char in context.characters:
        summary += f"\n- {char.name}: {char.summary}"
    return summary
