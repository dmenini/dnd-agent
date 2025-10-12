from pydantic import BaseModel

from agent.models.enums import ActionCategory, ActionType, DamageType, StatType, TargetingType


class ResourceCost(BaseModel):
    action_points: int = 1
    mana: int = 0
    ammo: int = 0
    cooldown: int = 0


class DecisionResult(BaseModel):
    action_id: str
    target_ids: list[str] = []
    description: str = ""


class ActionOption(BaseModel):
    id: str
    name: str
    source: str
    action_type: ActionType
    category: ActionCategory
    targeting: TargetingType
    resource_cost: ResourceCost
    damage_dice: str
    damage_type: DamageType
    magical_bonus: int = 0
    stat: StatType
    range: float
    meta: dict = {}


class Action(ActionOption):
    actor_id: str
    description: str
    target_ids: list[str]


COMBAT_ACTION_TYPES = {
    ActionType.MELEE_ATTACK,
    ActionType.RANGED_ATTACK,
    ActionType.SPELL,
    ActionType.AOE_SPELL,
    ActionType.SPECIAL,
}
