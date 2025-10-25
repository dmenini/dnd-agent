from typing import Any, Self

from pydantic import BaseModel, ConfigDict, computed_field

from agent.character.resolvers.effect import EffectResolver
from agent.character.resolvers.equipment import EquipmentResolver
from agent.character.resolvers.job import JobResolver
from agent.character.resolvers.roll import RollResolver
from agent.character.resources import ActionEconomy, SpellSlots
from agent.logs.events import Icon, LogLevel
from agent.models.position import Position


class Party(BaseModel):
    id: str
    name: str
    is_player_party: bool = False


class Character(EffectResolver, EquipmentResolver, RollResolver, JobResolver):
    party: Party

    spell_slots: SpellSlots = SpellSlots()
    action_economy: ActionEconomy = ActionEconomy()
    turn_done: bool = True

    model_config = ConfigDict(extra="allow")  # To mock during tests

    def model_post_init(self, _: Any, /) -> None:
        self.equip_all()
        self.apply_job_features()

        # Assign attributes
        self.attributes.hp = self.max_hp

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_speed(self) -> float:
        return self.attributes.speed() - self.action_economy.movement_used

    def move(self, destination: Position) -> None:
        self.pos = destination
        self.log_event(f"New position: {destination}", icon=Icon.MOVE)

    def hide(self) -> None:
        roll = self.stealth_roll()
        self.stealth_value = roll.total
        self.is_hidden = True
        self.log_event(f"{self.name} hides (Stealth {roll.total})", icon=Icon.STEALTH, show_ai=True)

    def unhide(self) -> None:
        self.is_hidden = False
        self.stealth_value = 0
        self.log_event(f"{self.name} is not hidden anymore!", icon=Icon.STEALTH, show_ai=True)

    def start_turn(self) -> None:
        self.log_event(f"{self.name} starts turn", event_type=LogLevel.DEBUG)
        self.turn_done = False
        self.action_economy.restore_turn()
        self.try_expire_effects(is_start=True)

    def end_turn(self) -> None:
        self.log_event(f"{self.name} ends turn", event_type=LogLevel.DEBUG)
        self.try_expire_effects(is_start=False)
        self.turn_done = True

    def end_round(self) -> None:
        self.action_economy.restore_reaction()

    def end_combat(self) -> None:
        # TODO: This should be done on rest
        for ability in self.abilities:
            if hasattr(ability, "rest"):
                ability.rest()

    def has_resources(self) -> bool:
        has_bonus = self.off_hand is not None and (self.action_economy.can_use_bonus())
        main_hand = self.main_hand or self.ranged or self.spells
        has_main = main_hand is not None and (self.action_economy.can_use_standard())
        has_movement = self.action_economy.can_move(self.current_speed)
        return has_main or has_bonus or has_movement

    def detect_target(self: Self, target: Self, *, use_passive: bool = False) -> bool:
        if not target.is_hidden:
            return True  # Always visible if not hidden

        # Use passive perception or active roll
        perception_value = self.attributes.passive_perception() if use_passive else self.perception_roll().total

        return perception_value >= (target.stealth_value or 0)
