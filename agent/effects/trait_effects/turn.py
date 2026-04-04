from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.actions.base import ActionType
from agent.character.resources import ActionExtension
from agent.effects.base import register_effect
from agent.models.constants import TRAIT_LOG_LEVEL

if TYPE_CHECKING:
    from agent.character.character import Character


@register_effect()
def cannot_move_effect(target: Character) -> None:
    target.action_economy.movement_available = False
    target.log_event(f"{target.name} cannot move this turn.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def cannot_act_effect(target: Character) -> None:
    target.action_economy.can_act = False
    target.log_event(f"{target.name} cannot act this turn.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def extra_actions_effect(target: Character, extensions: list[ActionExtension]) -> None:
    target.action_economy.action_extensions.extend(extensions)
    target.log_event(f"{target.name} gains {len(extensions)} extra actions.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def half_attacks_effect(target: Character) -> None:
    economy = target.action_economy
    attack_extensions = [
        ext
        for ext in economy.action_extensions
        if ext.category.STANDARD and ext.allowed_actions and ActionType.ATTACK in ext.allowed_actions
    ]
    keep_count = math.ceil(len(attack_extensions) / 2)
    for ext in attack_extensions[keep_count:]:
        economy.action_extensions.remove(ext)
    if attack_extensions[keep_count:]:
        target.log_event(f"{target.name}'s available attacks reduced to {keep_count}.", log_type=TRAIT_LOG_LEVEL)
