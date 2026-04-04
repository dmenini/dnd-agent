from __future__ import annotations

import math
from collections import deque
from typing import TYPE_CHECKING, Any

import numpy as np
import tcod
from pydantic import BaseModel, Field, field_validator, model_validator

from agent.models.position import Position

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agent.character.character import Character

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

    def update_map(self, characters: Mapping[str, Character]) -> None:
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

    def find_nearest(self, origin: Position, max_range: float | None = None) -> list[str]:
        # Compute (char_id, distance) pairs
        distances = [(char_id, origin.manhattan_distance(pos)) for char_id, pos in self.characters.items()]

        # If max_range is provided, filter out characters outside the range
        if max_range is not None:
            distances = [(char_id, dist) for char_id, dist in distances if dist <= max_range]

        # Sort by distance
        distances.sort(key=lambda item: item[1])

        # Return only the character IDs
        return [char_id for char_id, _ in distances]

    def get_visible_positions(self, observer: Character) -> set[Position]:
        """
        Compute visible tiles. Walls are included in the visible positions if they are in sight.
        """
        visible = set()

        # Observer position and attributes
        cx, cy = observer.pos.x, observer.pos.y
        radius = int(observer.attributes.vision_range())
        fov_angle = float(observer.attributes.base_vision_fov)  # degrees
        fx, fy = observer.pos.facing_vector

        # Create a 2D numpy array marking transparency (True = transparent)
        transparency_mask = self._transparency_mask()

        # Compute FOV using recursive symmetric shadowcasting. Examples:
        # R=8               R=3 no walls
        # #.....+++#        ..........
        # #...##+++#        ...+++++..
        # #+..+#+++#        ...+++++..
        # #+++#++++#        ...++@++..
        # #++++@+++#        ...+++++..
        # #++++++#.#        ...+++++..
        # #+++##++.#        ..........
        # #++...+++#
        fov_mask = tcod.map.compute_fov(
            transparency_mask,
            (cy, cx),  # tcod uses (row, col) = (y, x)
            radius=radius,
            light_walls=True,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
        )

        # Precompute cosine of half-angle for dot product test
        cos_half = math.cos(math.radians(fov_angle / 2.0))

        # Always see own tile
        center = Position(x=cx, y=cy)
        visible.add(center)

        # Iterate tcod-visible positions
        ys, xs = np.where(fov_mask)
        for y, x in zip(ys, xs, strict=False):
            pos = Position(x=x, y=y)
            if pos == center:
                continue

            dir_vec = observer.pos.direction_to(pos)
            dot = fx * dir_vec[0] + fy * dir_vec[1]

            if dot >= cos_half:
                visible.add(pos)

        return visible

    def is_walkable(self, x: int, y: int) -> bool:
        return (0 <= x < self.width) and (0 <= y < self.height) and (Position(x=x, y=y) not in self.walls)

    def within_visibility_range(self, observer: Character, target: Position) -> bool:
        """Check whether the target is visible to the actor, considering range and walls."""
        observer_pos = observer.pos

        if observer_pos == target:
            return True

        # 1. Distance check
        distance = observer_pos.euclidean_distance(target)
        if distance > observer.attributes.vision_range():
            return False

        # 2. Vision cone check
        if not self.in_vision_cone(observer, target):
            return False

        # 3. Line of sight check (Bresenham's line)
        return self.has_line_of_sight(observer, target)

    def in_vision_cone(self, observer: Character, target: Position) -> bool:
        """Return True if target is within observer's vision cone."""
        facing_x, facing_y = observer.pos.facing_vector
        tx, ty = observer.pos.direction_to(target)

        cos_half = math.cos(math.radians(observer.attributes.base_vision_fov / 2))
        dot = facing_x * tx + facing_y * ty
        return dot >= cos_half

    def has_line_of_sight(self, observer: Character, target: Position) -> bool:
        """Fast line-of-sight using libtcod's Bresenham algorithm."""
        # Build a local transparency map
        transparency_mask = self._transparency_mask()

        start = (observer.pos.y, observer.pos.x)
        end = (target.y, target.x)
        # tcod returns all tiles in the line, inclusive of endpoints
        line = tcod.los.bresenham(start, end).tolist()

        # If any step is non-transparent → blocked
        return all(transparency_mask[y, x] for y, x in line)

    def _transparency_mask(self) -> np.ndarray:
        transparency = np.ones((self.height, self.width), dtype=bool)
        for wall in self.walls:
            if 0 <= wall.y < self.height and 0 <= wall.x < self.width:
                transparency[wall.y, wall.x] = False
        return transparency

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
