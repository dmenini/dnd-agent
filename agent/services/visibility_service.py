from typing import TYPE_CHECKING

from agent.effects.traits import TraitBuilder
from agent.logs.log_event import Icon
from agent.models.enums import FeatureId
from agent.services.roll_service import RollService

if TYPE_CHECKING:
    from agent.character.character import Character


class VisibilityService:
    """Stateless service for managing character visibility (stealth and perception)."""

    @classmethod
    def hide(cls, character: "Character") -> None:
        """Make character attempt to hide using stealth."""
        roll = RollService.stealth_roll(character)
        character.stealth_value = roll.total
        trait = TraitBuilder.target_advantage(source_id="hide")
        character.register_passive(trait)
        character.log_event(f"{character.name} hides (stealth {roll.total})", icon=Icon.STEALTH, show_ai=True)

    @classmethod
    def unhide(cls, character: "Character") -> None:
        """Make character visible again."""
        character.stealth_value = 0
        character.unregister_passive(feature_id=FeatureId.ATTACKER_ADVANTAGE, source_id="hide")
        character.log_event(f"{character.name} is not hidden anymore!", icon=Icon.STEALTH, show_ai=True)

    @classmethod
    def detect_target(cls, observer: "Character", target: "Character", *, use_passive: bool = False) -> bool:
        """Check if observer can detect a target (accounts for stealth)."""
        if not target.is_hidden:
            return True  # Always visible if not hidden

        # Use passive perception or active roll
        perception_value = (
            observer.attributes.passive_perception() if use_passive else RollService.perception_roll(observer).total
        )

        return perception_value >= (target.stealth_value or 0)
