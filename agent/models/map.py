from __future__ import annotations

import math
from collections import deque
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from agent.models.position import Position

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agent.character.resolvers.base import CharacterBase

WALL_CELL = "#  "
EMPTY_CELL = "·  "
DIRECTION_ICON = {"N": "↑", "S": "↓", "E": "→", "W": "←", "NE": "↗", "NW": "↖", "SE": "↘", "SW": "↙"}


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

    @model_validator(mode="after")
    def validate_inbound(self) -> Any:
        for id_, pos in self.characters.items():
            if not is_inbound(pos, width=self.width, height=self.height):
                msg = (
                    f"Character {id_} position ({pos.x}, {pos.y}) is out of"
                    f" map bounds (0-{self.width - 1}, 0-{self.height - 1})"
                )
                raise ValueError(msg)

        # Remove outbound walls
        self.walls = [pos for pos in self.walls if is_inbound(pos, width=self.width, height=self.height)]

        return self

    def update_map(self, characters: Mapping[str, CharacterBase]) -> None:
        updated = {cid: characters[cid].pos for cid in self.characters if characters[cid].is_alive}
        self.characters = updated

    def distance(self, start: Position, end: Position) -> float | None:
        """Return shortest distance between two points considering obstacles using BFS-based search."""
        if (start.x, start.y) == (end.x, end.y):
            return 0

        visited = set()
        queue = deque([(start.x, start.y, 0)])  # (x, y, distance)

        while queue:
            x, y, dist = queue.popleft()

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # up, right, down, left
                nx, ny = x + dx, y + dy

                if (nx, ny) == (end.x, end.y):
                    return dist + 1

                if not self.is_walkable(nx, ny):
                    continue

                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))

        return None  # unreachable

    def is_walkable(self, x: int, y: int) -> bool:
        return (0 <= x < self.width) and (0 <= y < self.height) and (Position(x=x, y=y) not in self.walls)

    def within_visibility_range(self, observer: CharacterBase, target: CharacterBase) -> bool:
        """Check whether the target is visible to the actor, considering range and walls."""
        observer_pos = observer.pos
        target_pos = target.pos

        if observer_pos == target_pos:
            return True

        # 1. Distance check
        distance = observer_pos.euclidean_distance(target_pos)
        if distance > observer.attributes.vision_range():
            return False

        # 2. Vision cone check
        if not self.in_vision_cone(observer, target):
            return False

        # 3. Line of sight check (Bresenham's line)
        return self.has_line_of_sight(observer, target)

    def in_vision_cone(self, observer: CharacterBase, target: CharacterBase) -> bool:
        """Return True if target is within observer's vision cone."""
        facing_x, facing_y = observer.pos.facing_vector
        tx, ty = observer.pos.direction_to(target.pos)

        dot = facing_x * tx + facing_y * ty
        dot = max(-1.0, min(1.0, dot))  # numerical stability

        angle = math.degrees(math.acos(dot))
        return angle <= observer.attributes.base_vision_fov / 2

    def has_line_of_sight(self, observer: CharacterBase, target: CharacterBase) -> bool:
        observer_pos = observer.pos
        target_pos = target.pos
        for x, y in self._bresenham_line(observer_pos, target_pos):
            # If any wall blocks the view, line of sight is broken
            if any(wall.x == x and wall.y == y for wall in self.walls):
                return False
        return True

    def _bresenham_line(self, start: Position, end: Position) -> list[tuple[int, int]]:
        """
        Compute the grid cells traversed by a straight line between two positions using Bresenham's algorithm.
        Excludes the starting point, but includes all intermediate cells up to (but not including) the end point.
        """
        points = []

        # Initialize coordinates
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y

        # Compute deltas (absolute distances along x and y)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        # Determine the step direction for x and y
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        # Error term (difference between ideal line and rasterized line)
        err = dx - dy

        # Start at the initial position and iterate until we reach the end position
        x, y = x0, y0
        while (x, y) != (x1, y1):
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x += sx  # Move horizontally
            if e2 < dx:
                err += dx
                y += sy  # Move vertically

            # Add intermediate points (exclude the final cell)
            if (x, y) != (x1, y1):
                points.append((x, y))

        return points

    def __str__(self) -> str:
        self.map = "\n".join(" ".join(row) for row in self.grid)
        return self.map

    @property
    def grid(self) -> list[list[str]]:
        grid = [[EMPTY_CELL for _ in range(self.width)] for _ in range(self.height)]

        for wall in self.walls:
            grid[wall.y][wall.x] = WALL_CELL

        for key, char in self.characters.items():
            grid[char.y][char.x] = f"{self.icons[key]}{DIRECTION_ICON[char.direction]}"

        return grid
