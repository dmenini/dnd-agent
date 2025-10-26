from functools import total_ordering
from math import sqrt
from typing import Self

from pydantic import BaseModel


@total_ordering
class Position(BaseModel):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

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
        return sqrt(dx * dx + dy * dy)
