from agent.actions.base import ActionCategory, ActionType
from agent.character.resources import ActionExtension
from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.lethargic import Lethargic
from agent.effects.traits import ACBonus, AdvantageOnSavingThrow, ExtraActions, SpeedMultiplier, Trait


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

    _traits: list[Trait] = [
        ExtraActions(
            extensions=[
                ActionExtension(
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
            ]
        ),
        SpeedMultiplier(value=2),
        ACBonus(value=2),
        AdvantageOnSavingThrow(stat=StatType.DEX),
    ]
    followup: StatusEffect = Lethargic(duration=1)
