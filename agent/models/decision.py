from collections.abc import Mapping

from pydantic import BaseModel, Field, computed_field

from agent.actions.base import Action
from agent.actions.common.dash import DashAction
from agent.character.character import Character
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.position import Position


class DecisionResult(BaseModel):
    action_id: str = Field(..., description="ID of the action to take")

    # Map of target ID → number of hits assigned
    target_hits: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Mapping of target IDs to number of hits each target should receive.\n"
            f"Example for {TargetingType.MULTI} targeting attack (3 total hits): {{'enemy1': 2, 'enemy2': 1}}\n"
            f"Example for {TargetingType.SINGLE} targeting attack (2 total hits): {{'enemy1': 2}}\n"
            f"Example for {TargetingType.SELF} targeting attack: {{}}"
        ),
    )

    target_position: Position | None = Field(
        default=None,
        description="Target position in case of movement actions. It must be within range.",
    )

    description: str = Field(description="Action description for narrative purpose.")

    @computed_field()  # type: ignore[prop-decorator]
    @property
    def total_hits(self) -> int:
        """Total number of hits to perform (sum of all target hits)."""
        return sum(self.target_hits.values())

    @computed_field()  # type: ignore[prop-decorator]
    @property
    def target_ids(self) -> list[str]:
        """All targeted IDs."""
        return list(self.target_hits.keys())

    def autocorrect(self, action: Action) -> None:
        """Lightweight autocorrection before validation.

        This method fixes only simple, mechanical issues:
          * Trims excessive targets for SINGLE and MULTI actions.
          * Reduces hit counts to the action's maximum limit.
          * Removes target data for area actions (uses position only).
          * Removes position data for non-area actions.
        """
        # Remove irrelevant position data
        if action.targeting != TargetingType.AREA:
            self.target_position = None
        elif action.targeting == TargetingType.AREA:
            self.target_hits.clear()  # Area actions shouldn't have target hits

        # For actions involving specific targets
        if self.target_hits:
            if action.targeting == TargetingType.SINGLE:
                # Keep only the first target
                first_target, hits = next(iter(self.target_hits.items()))
                self.target_hits = {first_target: min(hits, action.hits)}

            elif action.targeting == TargetingType.MULTI:
                # Trim to allowed number of targets and hits
                items = list(self.target_hits.items())[: action.hits]
                corrected = {}
                total_hits = 0
                for target, hits in items:
                    if total_hits >= action.hits:
                        break
                    allowed_hits = min(hits, action.hits - total_hits)
                    corrected[target] = allowed_hits
                    total_hits += allowed_hits
                self.target_hits = corrected

            elif action.targeting == TargetingType.SELF:
                # Self actions should not have any target
                self.target_hits.clear()

    def validate_self_targeting(self, actor_id: str) -> tuple[bool, str]:
        msg = ""
        if self.target_ids and self.target_ids != [actor_id]:
            msg = (
                f"Action {self.action_id} targets SELF only, but received other targets. "
                f"Please target only the acting entity itself."
            )
        return msg == "", msg

    def validate_area_targeting(self) -> tuple[bool, str]:
        msg = ""
        if not isinstance(self.target_position, Position):
            msg = (
                f"Action {self.action_id} targets an area of effect and requires a target position "
                f"(x, y coordinates). Please provide a valid position instead of entity targets."
            )
        elif self.target_ids:
            msg = (
                f"Action {self.action_id} targets an area, not specific entities. "
                f"Please remove any target IDs and specify only the position."
            )
        return msg == "", msg

    def validate_single_targeting(self, action: Action) -> tuple[bool, str]:
        msg = ""
        if not self.target_ids:
            msg = (
                f"Action {self.action_id} requires at least one valid target ID, but none were provided. "
                f"Please specify which entity or entities to attack."
            )
        elif action.targeting == TargetingType.SINGLE:
            if len(self.target_ids) > 1:
                msg = (
                    f"Action {self.action_id} targets only one enemy, but received {len(self.target_ids)} targets. "
                    f"Please provide exactly one target ID."
                )
            elif self.total_hits > action.hits:
                msg = (
                    f"Action {self.action_id} allows up to {action.hits} hit(s) on a single target, "
                    f"but {self.total_hits} hits were assigned. Please reduce the hit count."
                )
        return msg == "", msg

    def validate_multi_targeting(self, action: Action) -> tuple[bool, str]:
        msg = ""
        if self.total_hits > action.hits:
            msg = (
                f"Action {self.action_id} allows at most {action.hits} total hit(s) distributed among all targets, "
                f"but {self.total_hits} hits were assigned. Please adjust hit distribution accordingly."
            )

        return msg == "", msg

    def validate_targets_exist(self, characters: Mapping[str, Character]) -> tuple[bool, str]:
        for target_id in self.target_ids:
            if target_id not in characters:
                return False, f"Target '{target_id}' not found. Please, retry with a valid target."
        return True, ""

    def validate_targets_alive(self, characters: Mapping[str, Character]) -> tuple[bool, str]:
        for target_id in self.target_ids:
            target = characters[target_id]
            if not target.is_alive:
                return False, f"Target '{target.id}' is already down. Please, choose another target."
        return True, ""

    def validate_friendly_fire(
        self,
        actor: Character,
        characters: Mapping[str, Character],
    ) -> tuple[bool, str]:
        for target_id in self.target_ids:
            target = characters[target_id]
            if actor.party.id == target.party.id:
                return False, f"{actor.id} cannot attack ally {target.id}. Please, select enemies instead."
        return True, ""

    def validate_range(
        self,
        actor: Character,
        characters: Mapping[str, Character],
        available_movement: int,
    ) -> tuple[bool, str]:
        # For range, we use simple line-of-sight distance, assuming that walls can be ignored by attacks
        for target_id in self.target_ids:
            target = characters[target_id]
            dist = actor.los_distance(target.pos)
            if dist > available_movement:
                return (
                    False,
                    (
                        f"Target '{target.id}' is out of range ({dist:.1f}m > {available_movement}m). "
                        f"Please, choose a closer target."
                    ),
                )
        return True, ""

    def validate_movement(
        self,
        actor: Character,
        action: Action,
        game_map: GameMap,
    ) -> tuple[bool, str]:
        pos = self.target_position
        if not pos:
            return False, f"No target position specified for movement action {self.action_id}."

        if not (0 <= pos.x < game_map.width and 0 <= pos.y < game_map.height):
            return (
                False,
                f"Target position ({pos.x}, {pos.y}) is out of map bounds "
                f"(0-{game_map.width - 1}, 0-{game_map.height - 1}).",
            )

        # For movement, we use distance measured on the map with pathfinding algo
        multiplier = 2 if isinstance(action, DashAction) else 1
        dist = game_map.distance(start=actor.pos, end=pos)
        max_dist = actor.current_speed * multiplier
        if dist is None:
            return (
                False,
                f"Position {pos} cannot be reached. Please, try a different one.",
            )
        if dist > max_dist:
            return (
                False,
                f"Position {pos} is too far ({dist:.1f}m > {max_dist}m). Please, select a closer position.",
            )

        occupied_positions = list(game_map.characters.values()) + game_map.walls
        if pos in occupied_positions:
            return False, f"Position {pos} is already occupied. Please, choose a nearby position."

        return True, ""
