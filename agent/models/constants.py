from agent.logs.events import LogLevel


class FeatureId:
    SECOND_WIND_ID = "second_wind"
    FIGHTING_STYLE_DEFENSE = "fighting_style_defense"


class EventType:
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    APPLY_DAMAGE = "apply_damage"
    RECEIVE_DAMAGE = "receive_damage"


TRAIT_LOG_LEVEL = LogLevel.DEBUG
