from enum import Enum

from agent.logs.log_event import LogLevel


class EventType(str, Enum):
    MODIFIER = "modifier"  # Execute immediately
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    APPLY_DAMAGE = "apply_damage"
    RECEIVE_DAMAGE = "receive_damage"


MELEE_RANGE = 5
BONUS_AC_FROM_SHIELDS = 2

TRAIT_LOG_LEVEL = LogLevel.DEBUG
