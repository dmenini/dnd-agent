"""Helper to load spell actions for job definitions.

This is temporary - helps us load ComposableAction instances from JSON files
for testing. In production, the DM will create ComposableAction instances directly.
"""

from pathlib import Path

from agent.actions.composable import ComposableAction
from agent.actions.loader import ActionLoader


def load_spell(json_filename: str) -> ComposableAction:
    """Load a spell action from JSON file.

    Args:
        json_filename: Name of JSON file in actions/definitions/

    Returns:
        ComposableAction instance

    Note: This is for testing/development only. In production, spells will be
    created as ComposableAction instances directly by the DM.
    """
    definitions_dir = Path(__file__).parent.parent / "actions" / "definitions"
    json_path = definitions_dir / json_filename
    return ActionLoader.from_file(str(json_path))
