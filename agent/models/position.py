import math
from functools import total_ordering
from typing import Literal, Self

from pydantic import BaseModel

# Pre-normalised direction vectors (y increases downward).
DIRECTION_VECTORS = {
    "N": (0, 1),
    "S": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
    "NE": (math.sqrt(0.5), math.sqrt(0.5)),
    "NW": (-math.sqrt(0.5), math.sqrt(0.5)),
    "SE": (math.sqrt(0.5), -math.sqrt(0.5)),
    "SW": (-math.sqrt(0.5), -math.sqrt(0.5)),
}


@total_ordering
class Position(BaseModel):
    x: int
    y: int
    direction: Literal["N", "S", "E", "W", "NE", "NW", "SE", "SW"] = "N"

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.direction})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Position):
            raise TypeError
        return self.x < other.x and self.y < other.y

    def __hash__(self) -> int:
        return hash(self.x) + hash(self.y)

    def manhattan_distance(self, other: Self) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def euclidean_distance(self, other: Self) -> float:
        dx = other.x - self.x
        dy = other.y - self.y
        return math.hypot(dx, dy)

    def direction_to(self, other: Self) -> tuple[float, float]:
        dx, dy = other.x - self.x, self.y - other.y  # account for negative y-axis
        dist = math.hypot(dx, dy)
        if dist == 0:
            return 0.0, 0.0
        return dx / dist, dy / dist

    @property
    def facing_vector(self) -> tuple[float, float]:
        """Facing direction as a 2D vector."""
        return DIRECTION_VECTORS[self.direction]
