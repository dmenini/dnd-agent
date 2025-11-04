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


# Traditionally is 5, but in our map it looks weird to be able to attack a target 5 tiles away
MELEE_RANGE = 2

BONUS_AC_FROM_SHIELDS = 2

TRAIT_LOG_LEVEL = LogLevel.DEBUG
