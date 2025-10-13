from pydantic import BaseModel, Field


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
