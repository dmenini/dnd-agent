from __future__ import annotations

from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime  # noqa: TC002
from langgraph.types import Command

from agent.character.builder import CharacterBuilder, CharacterSelections, options_map
from agent.jobs.base import JobType


@tool
def get_class_options(job_type: JobType) -> str:
    """
    Get available options for a character class (subclass, skills, equipment).

    Returns:
        Formatted string describing all available options.
    """
    options = options_map.get(job_type)
    if not options:
        return f"No detailed options found for {job_type.value}"

    return options.model_dump_json()


@tool
def save_base_character(character: CharacterBuilder, runtime: ToolRuntime) -> Command:
    """
    Never call this tool without player confirmation!

    Persist the base character information. Behaves like a PUT.
    After this, guide the player through selecting subclass, skills, equipment.

    Returns:
        Next steps message.
    """
    builder = runtime.state.get("current_builder")
    if not builder:
        msg = (
            f"Character saved!\n\n"
            f"{character.model_dump_json(exclude={'selections'})}\n\n"
            f"As a next step, the player must choose their subclass, skills, equipment. "
            f"Use get_class_options to see what's available."
        )
    else:
        # The tool can also be used to update existing fields, but not selections
        existing = CharacterBuilder.model_validate(builder)
        character.selections = existing.selections
        msg = f"Character saved!\n\n{character.model_dump_json(exclude={'selections'})}"

    return _format_tool_response(current_builder=character, message=msg, tool_call_id=runtime.tool_call_id)


@tool
def save_skills(selections: CharacterSelections, runtime: ToolRuntime) -> Command:
    """
    Call this every time the player chooses skill proficiencies to persist them.
    Requires the character builder previously initialized for this character.

    Returns:
        Updated character model
    """
    if not runtime.state["current_builder"]:
        msg = "No character is currently being created. Use save_base_character first."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    options = options_map.get(runtime.state["current_builder"].job)
    if not options:
        msg = "Cannot set player selections - no options available for this class."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    try:
        selections.validate_skills(options.skill_options, options.skill_count)
    except ValueError as e:
        return _format_tool_response(message=str(e), tool_call_id=runtime.tool_call_id)

    builder = runtime.state["current_builder"].model_copy(deep=True)

    builder.selections.skill_proficiencies = selections.skill_proficiencies

    msg = f"Skills set!\n\n{builder.model_dump_json()}"
    return _format_tool_response(
        current_builder=builder,
        message=msg,
        tool_call_id=runtime.tool_call_id,
    )


@tool
def save_subclass(selections: CharacterSelections, runtime: ToolRuntime) -> Command:
    """
    Call this every time the player chooses a subclass to persist it.
    Requires the character builder previously initialized for this character.

    Returns:
        Updated character model
    """
    if not runtime.state["current_builder"]:
        msg = "No character is currently being created. Use save_base_character first."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    options = options_map.get(runtime.state["current_builder"].job)
    if not options:
        msg = "Cannot set player selections - no options available for this class."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    builder = runtime.state["current_builder"].model_copy(deep=True)

    builder.selections.subclass = selections.subclass

    msg = f"Subclass set!\n\n{builder.model_dump_json()}"
    return _format_tool_response(
        current_builder=builder,
        message=msg,
        tool_call_id=runtime.tool_call_id,
    )


@tool
def save_starting_equipment(selections: CharacterSelections, runtime: ToolRuntime) -> Command:
    """
    Call this every time the player chooses equipments to persist them.
    Requires the character builder previously initialized for this character.

    Returns:
        Updated character model
    """
    if not runtime.state["current_builder"]:
        msg = "No character is currently being created. Use save_base_character first."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    options = options_map.get(runtime.state["current_builder"].job)
    if not options:
        msg = "Cannot set player selections - no options available for this class."
        return _format_tool_response(message=msg, tool_call_id=runtime.tool_call_id)

    try:
        selections.validate_equipment_choices(options.equipment_options)
    except ValueError as e:
        return _format_tool_response(message=str(e), tool_call_id=runtime.tool_call_id)

    builder = runtime.state["current_builder"].model_copy(deep=True)

    for slot, eq in selections.equipment.items():
        builder.selections.equipment[slot] = eq

    msg = f"Starting equipment set!\n\n{builder.model_dump_json()}"
    return _format_tool_response(
        current_builder=builder,
        message=msg,
        tool_call_id=runtime.tool_call_id,
    )


@tool
def finalize_character(runtime: ToolRuntime) -> Command:
    """
    Call this after all narrative and mechanical choices (skills, equipment, subclass) are made
    to finalize the creation of the current character.

    Returns:
        Confirmation message
    """
    builder = runtime.state["current_builder"]
    if not builder:
        msg = "No character is currently being created."
        return _format_tool_response(msg, runtime.tool_call_id)

    # Validate all required choices are made
    options = options_map.get(builder.job)
    if options:
        # Check skills
        if options.skill_options and len(builder.selections.skill_proficiencies) != options.skill_count:
            msg = f"Must choose {options.skill_count} skills before finalizing."
            return _format_tool_response(msg, runtime.tool_call_id)

        # Check equipment
        if options.equipment_options:
            missing_equipment = [
                e.slot for e in options.equipment_options if e.slot not in builder.selections.equipment
            ]
            if missing_equipment:
                msg = f"Missing equipment choices: {missing_equipment}"
                return _format_tool_response(msg, runtime.tool_call_id)

        # Check subclass
        if options.subclass_options.level_required == 1 and not builder.selections.subclass:
            msg = "Missing subclass"
            return _format_tool_response(msg, runtime.tool_call_id)

    # Save character
    msg = "Character creation complete"

    return _format_tool_response(
        current_builder=None,
        done=len(runtime.state["party"]) + 1 == runtime.state["max_players"],
        party=[builder],
        message=msg,
        tool_call_id=runtime.tool_call_id,
    )


@tool
def get_party_status(runtime: ToolRuntime) -> str:
    """
    Get the current status of party creation.

    Returns:
        Summary of current characters and maximum allowed.
    """
    max_players = runtime.state["max_players"]
    party = runtime.state["party"]
    remaining = max_players - len(party)

    if remaining > 0:
        summary = f"Players have created {len(party)}/{max_players} character(s)"
        for char in party:
            summary += f"\n- {char.name}: {char.summary}"

        if runtime.state["current_builder"]:
            summary += f"\n\nCurrently creating: {runtime.state['current_builder'].name}"
        else:
            summary += f"\n\nThey can create {remaining} more."

        return summary

    return f"Players have created the maximum of {max_players} characters! Party is complete."


@tool
def finalize_party(runtime: ToolRuntime) -> Command:
    """
    Finalize the character creation process.
    Call this as soon as the player is done creating the party or maximum is reached.
    The story cannot proceed unless this tool is called.

    Returns:
        Summary of the created party.
    """
    party = runtime.state["party"]
    max_players = runtime.state["max_players"]
    summary = f"Party complete with {len(party)}/{max_players} character(s):\n"
    for char in party:
        summary += f"\n- {char.name}: {char.summary}"

    summary += "\n\nCongratulate the player and ask if they want to start the adventure"

    return _format_tool_response(
        done=True,
        message=summary,
        tool_call_id=runtime.tool_call_id,
    )


def _format_tool_response(message: str, tool_call_id: str | None, **kwargs: Any) -> Command:
    return Command(update={**kwargs, "messages": [ToolMessage(content=message, tool_call_id=tool_call_id)]})
