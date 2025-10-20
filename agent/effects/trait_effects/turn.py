from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.actions.base import ActionType
from agent.character.resources import ActionExtension
from agent.logs.events import LogLevel

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


def cannot_move_effect(target: CharacterBase) -> None:
    target.action_economy.movement_available = False
    target.log_event(f"{target.name} cannot move this turn.", event_type=LogLevel.DEBUG)


def cannot_act_effect(target: CharacterBase) -> None:
    target.action_economy.can_act = False
    target.log_event(f"{target.name} cannot act this turn.", event_type=LogLevel.DEBUG)


def extra_actions_effect(target: CharacterBase, extensions: list[ActionExtension]) -> None:
    target.action_economy.action_extensions.extend(extensions)
    target.log_event(f"{target.name} gains {len(extensions)} extra actions.", event_type=LogLevel.DEBUG)


def half_attacks_effect(target: CharacterBase) -> None:
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
        target.log_event(f"{target.name}'s available attacks reduced to {keep_count}.", event_type=LogLevel.DEBUG)
