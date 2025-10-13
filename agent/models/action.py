from pydantic import BaseModel, Field

from agent.models.enums import ActionCategory, ActionType, DamageType, StatType, TargetingType, WeaponType


class DecisionResult(BaseModel):
    action_id: str = Field(description="ID of the action to take")
    target_ids: list[str] = Field(
        default=[],
        description=(
            "IDs of the targets to attack for attack actions. Targets must be within range. "
            "Multiple targets can be attacked only with area actions."
        ),
    )
    target_position: tuple[int, int] | None = Field(
        default=None,
        description="Target position in case of movement actions. It must be within range.",
    )
    description: str = Field(description="Action description for narrative purpose.")


class ActionOption(BaseModel):
    id: str
    name: str
    source: str
    action_type: ActionType
    category: ActionCategory
    targeting: TargetingType
    damage_dice: str | None = None
    damage_type: DamageType | None = None
    weapon_type: WeaponType | None = None
    magical_bonus: int | None = None
    stat: StatType | None = None
    range: float
    meta: dict = {}


class Action(ActionOption):
    actor_id: str
    description: str
    target_ids: list[str]
    target_position: tuple[int, int] | None


COMBAT_ACTION_TYPES = {
    ActionType.MELEE_ATTACK,
    ActionType.RANGED_ATTACK,
    ActionType.SPELL,
    ActionType.AOE_SPELL,
    ActionType.SPECIAL,
}
