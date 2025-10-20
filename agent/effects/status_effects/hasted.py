from typing import Any

from agent.actions.base import ActionCategory, ActionType
from agent.character.resources import ActionExtension
from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.status_effects.lethargic import Lethargic
from agent.effects.traits import Trait
from agent.jobs.feature import FeatureId

StandardActionExtension = ActionExtension(
    source="haste",
    category=ActionCategory.STANDARD,
    allowed_actions=[
        ActionType.ATTACK,  # TODO: Limit to 1 hand attack or ranged
        ActionType.DASH,
        ActionType.DISENGAGE,
        ActionType.HIDE,
        ActionType.USE_OBJECT,
    ],
    requires_previous_action=True,
    expires_end_of_turn=True,
)


class Hasted(StatusEffect):
    """
    * Target speed is doubled.
    * Target gains a +2 bonus to AC.
    * Target has advantage on Dexterity saving throws.
    * Target gains an additional action on each of its turns (limited to Attack, Dash, Disengage, Hide, Use Object).
    When the effect ends, the target gets lethargy for 1 turn.
    """

    type: EffectType = EffectType.HASTED
    save_dc: int = 0  # Skip save throw as it's cast on a willing creature
    followup: StatusEffect = Lethargic(duration=1)

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.EXTRA_ACTIONS, extensions=[StandardActionExtension]),
            TraitRegistry.create(FeatureId.SPEED_MULTIPLIER, value=2),
            TraitRegistry.create(FeatureId.AC_BONUS, value=2),
            TraitRegistry.create(FeatureId.SAVE_ADVANTAGE, stat=StatType.DEX),
        ]
