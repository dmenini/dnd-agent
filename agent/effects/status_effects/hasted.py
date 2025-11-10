from agent.actions.base import ActionCategory, ActionType
from agent.character.abilities import AbilityType
from agent.character.resources import ActionExtension
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.effects.status_effects.lethargic import Lethargic
from agent.models.enums import FeatureId

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
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.EXTRA_ACTIONS, kwargs={"extensions": [StandardActionExtension]}),
        StatusEffectFeature(ref_id=FeatureId.SPEED_MULTIPLIER, kwargs={"value": 2}),
        StatusEffectFeature(ref_id=FeatureId.AC_BONUS, kwargs={"value": 2}),
        StatusEffectFeature(ref_id=FeatureId.SAVE_ADVANTAGE, kwargs={"ability": AbilityType.DEX}),
    ]
