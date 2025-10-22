from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from agent.models.position import Position


def is_inbound(pos: Position, width: int, height: int) -> bool:
    return 0 <= pos.x < width and 0 <= pos.y < height


class GameMap(BaseModel):
    map: str = Field(description="String representation of the map, abiding the given representation rules.")
    width: int = Field(ge=0, le=100, description="Width of the map.")
    height: int = Field(ge=0, le=50, description="Height of the map.")
    walls: list[Position] = Field(default=[], description="Position of walls in the generated map.")
    characters: dict[str, Position] = Field(default={}, description="Mapping character id to position.")
    icons: dict[str, str] = Field(default={}, description="Mapping character id to icon.")

    @field_validator("characters", mode="after")
    @classmethod
    def validate_not_overlapping(cls, val: dict[str, Position]) -> dict[str, Position]:
        positions = {str(pos) for pos in val.values()}
        if len(positions) < len(val):
            raise ValueError("Some characters share the same coordinates")

        return val

    @model_validator(mode='after')
    def validate_inbound(self) -> Any:
        for id_, pos in self.characters.items():
            if not is_inbound(pos, width=self.width, height=self.height):
                msg = (
                    f"Character {id_} position ({pos.x}, {pos.y}) is out of"
                    f" map bounds (0-{self.width - 1}, 0-{self.height - 1})"
                )
                raise ValueError(msg)

        # Remove outbound walls
        fixed_walls = []
        for pos in self.walls:
            if is_inbound(pos, width=self.width, height=self.height):
                fixed_walls.append(pos)
        self.walls = fixed_walls

        return self

    def is_walkable(self, x: int, y: int) -> bool:
        return (0 <= x < self.width) and (0 <= y < self.height) and ((x, y) not in self.walls)

    def __str__(self) -> str:
        grid = [["· " for _ in range(self.width)] for _ in range(self.height)]

        for wall in self.walls:
            grid[wall.y][wall.x] = "# "

        for key, char in self.characters.items():
            grid[char.y][char.x] = self.icons[key]

        return "\n".join(" ".join(row) for row in grid)
