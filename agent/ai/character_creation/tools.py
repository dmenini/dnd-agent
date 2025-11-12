from __future__ import annotations

from agent.character.abilities import SkillType
from agent.character.builder import CharacterBuilder, options_map
from agent.equipment.base import EquipmentSlot
from agent.jobs.base import JobType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.ai.character_creation.agent import CharacterCreationAgent


def get_class_options(job_type: JobType) -> str:
    options = options_map.get(job_type)
    if not options:
        return f"No detailed options found for {job_type.value}"

    result = f"Options for {job_type.value}:\n\n"

    # Skills
    result += f"**Skills** (choose {options.skill_count}):\n"
    for skill in options.skill_choices:
        result += f"  - {skill.value}\n"

    # Equipment
    if options.equipment_choices:
        result += "\n**Equipment Choices**:\n"
        for eq_choice in options.equipment_choices:
            result += f"  {eq_choice.slot.value} - {eq_choice.description}:\n"
            for opt in eq_choice.options:
                result += f"    - {opt}\n"

    # Features
    if options.feature_choices:
        result += "\n**Class Features**:\n"
        for feat_choice in options.feature_choices:
            result += f"  {feat_choice.feature_name} - {feat_choice.description}:\n"
            for opt in feat_choice.options:
                result += f"    - {opt}\n"

    return result


def start_character_creation(context: CharacterCreationAgent, character: CharacterBuilder) -> str:
    context._current_builder = character

    return (
        f"Started creating {character.name}, the {character.job.value}! "
        f"Now let's choose their skills, equipment, and features. "
        f"Use get_class_options_tool to see what's available."
    )


def set_skill_proficiencies(context: CharacterCreationAgent, skills: list[SkillType]) -> str:
    if not context._current_builder:
        return "No character is currently being created. Use start_character_creation first."

    options = options_map.get(context._current_builder.job)
    if not options:
        return "Cannot set skills - no options available for this class."

    # Validate selections
    invalid = [s for s in skills if s not in options.skill_choices]

    if invalid:
        return f"Invalid skill choices: {invalid}. Valid options: {options.skill_choices}"

    if len(skills) > options.skill_count:
        return f"Must choose exactly {options.skill_count} skills. You chose {len(skills)}."

    # Convert to SkillType enums and store
    skill_enums = [SkillType(s) for s in skills]
    context._current_builder.selections.skill_proficiencies = skill_enums

    return "Success: skills set!"


def set_equipment_choice(context: CharacterCreationAgent, slot: EquipmentSlot, choice: str) -> str:
    if not context._current_builder:
        return "No character is currently being created. Use start_character_creation first."

    options = options_map.get(context._current_builder.job)
    if not options:
        return "No equipment options for this class."

    # Find the equipment choice
    eq_choice = next((e for e in options.equipment_choices if e.slot == slot), None)
    if not eq_choice:
        return f"Invalid equipment slot: {slot}"

    if choice not in eq_choice.options:
        return f"Invalid choice '{choice}' for {slot}. Options: {eq_choice.options}"

    context._current_builder.selections.equipment[slot] = choice
    return f"Success: slot {slot.value} set to {choice}"


def set_feature_choice(context: CharacterCreationAgent, feature_name: str, choice: str) -> str:
    if not context._current_builder:
        return "No character is currently being created. Use start_character_creation first."

    options = options_map.get(context._current_builder.job)
    if not options:
        return "No feature options for this class."

    feat_choice = next((f for f in options.feature_choices if f.feature_name == feature_name), None)
    if not feat_choice:
        return f"Invalid feature: {feature_name}"

    # Check if choice matches any option (allow partial matching)
    matching_option = None
    for opt in feat_choice.options:
        if choice.lower() in opt.lower() or opt.lower().startswith(choice.lower()):
            matching_option = opt
            break

    if not matching_option:
        return f"Invalid choice for {feature_name}. Options: {feat_choice.options}"

    context._current_builder.selections.features[feature_name] = matching_option
    return f"Success: feature {feature_name} set to {matching_option}"


def finalize_character(context: CharacterCreationAgent) -> str:
    if not context._current_builder:
        return "No character is currently being created."

    # Validate all required choices are made
    options = options_map.get(context._current_builder.job)
    if options:
        # Check skills
        if len(context._current_builder.selections.skill_proficiencies) != options.skill_count:
            return f"Must choose {options.skill_count} skills before finalizing."

        # Check equipment
        missing_equipment = [
            e.slot for e in options.equipment_choices if e.slot not in context._current_builder.selections.equipment
        ]
        if missing_equipment:
            return f"Missing equipment choices: {missing_equipment}"

        # Check features
        missing_features = [
            f.feature_name
            for f in options.feature_choices
            if f.feature_name not in context._current_builder.selections.features
        ]
        if missing_features:
            return f"Missing feature choices: {missing_features}"

    # Save character
    context.characters.append(context._current_builder)
    msg = f"Character creation complete: {context._current_builder.name}"

    context._current_builder = None

    if len(context.characters) == context.max_players:
        context._done = True

    return msg


def get_party_status(context: CharacterCreationAgent) -> str:
    remaining = context.max_players - len(context.characters)

    if remaining > 0:
        summary = f"Players have created {len(context.characters)}/{context.max_players} character(s)"
        for char in context.characters:
            context += f"\n- {char.name}: {char.summary}"

        if context._current_builder:
            summary += f"\n\nCurrently creating: {context._current_builder.name}"
        else:
            summary += f"\n\nThey can create {remaining} more."

        return summary

    return f"Players have created the maximum of {context.max_players} characters! Party is complete."


def finalize_party(context: CharacterCreationAgent) -> str:
    context._done = True

    summary = f"Party complete with {len(context.characters)}/{context.max_players} character(s):\n"
    for char in context.characters:
        summary += f"\n- {char.name}: {char.summary}"
    return summary
