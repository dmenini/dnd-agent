from typing import Any

from pydantic import BaseModel, computed_field

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

    def model_post_init(self, _: Any, /) -> None:
        # Equip to apply traits
        self.equip_all()
        self.apply_job_features()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_speed(self) -> float:
        return self.attributes.speed() - self.action_economy.movement_used

    def move(self, destination: Position) -> None:
        self.pos = destination
        self.log_event(f"New position: {destination}", icon=Icon.MOVE)

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

    def has_resources(self) -> bool:
        has_bonus = self.off_hand is not None and (self.action_economy.can_use_bonus())
        main_hand = self.main_hand or self.ranged or self.spells
        has_main = main_hand is not None and (self.action_economy.can_use_standard())
        has_movement = self.action_economy.can_move(self.current_speed)
        return has_main or has_bonus or has_movement
