from typing import Any, Self

from pydantic import BaseModel, computed_field

from agent.actions.base import Action
from agent.actions.common.attack import MainHandAttackAction, OffHandAttackAction, RangedAttackAction
from agent.actions.common.dash import DashAction
from agent.actions.common.dodge import DodgeAction
from agent.actions.common.hide import HideAction
from agent.actions.common.move import MovementAction
from agent.actions.common.wait import WaitAction
from agent.character.resolvers.effect import EffectResolver
from agent.character.resolvers.equipment import EquipmentResolver
from agent.character.resolvers.job import JobResolver
from agent.character.resolvers.roll import RollResolver
from agent.character.resources import ActionEconomy, SpellSlots
from agent.character.stats import Stats
from agent.effects.traits import TargetAdvantageOnAttackRoll
from agent.equipment.weapons import MeleeWeapon
from agent.logs.events import Icon
from agent.models.enums import FeatureId
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
        self.equip_all()
        self.apply_job_features()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_speed(self) -> float:
        return self.attributes.speed() - self.action_economy.movement_used

    def move(self, destination: Position) -> None:
        starting_pos = self.pos.model_copy()
        self.pos = destination
        self.log_event(f"{self.name} moves from {starting_pos} to {destination}", icon=Icon.MOVE)

    def hide(self) -> None:
        roll = self.stealth_roll()
        self.stealth_value = roll.total
        trait = TargetAdvantageOnAttackRoll(feature_id=FeatureId.STEALTH, source_id="hide")
        self.register_passive(trait)
        self.log_event(f"{self.name} hides (stealth {roll.total})", icon=Icon.STEALTH, show_ai=True)

    def unhide(self) -> None:
        self.stealth_value = 0
        self.unregister_passive(feature_id=FeatureId.STEALTH, source_id="hide")
        self.log_event(f"{self.name} is not hidden anymore!", icon=Icon.STEALTH, show_ai=True)

    def start_turn(self) -> None:
        self.turn_done = False
        self.action_economy.restore_turn()
        self.try_expire_effects(is_start=True)

    def end_turn(self) -> None:
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

    def get_available_actions(self) -> dict[str, Action]:
        all_actions: list[Action] = [
            MovementAction(range=self.current_speed),
            DashAction(range=self.current_speed),
            DodgeAction(),
            WaitAction(),
            HideAction(),
        ]

        # Equipment-based actions
        if self.main_hand:
            main_action = MainHandAttackAction.from_weapon(
                weapon=self.main_hand, is_two_handed=self.two_handed_active, stats=self.attributes
            )
            all_actions.append(main_action)
        if self.off_hand and isinstance(self.off_hand.type, MeleeWeapon):
            off_action = OffHandAttackAction.from_weapon(weapon=self.off_hand)
            all_actions.append(off_action)
        if self.ranged:
            ranged_action = RangedAttackAction.from_weapon(weapon=self.ranged)
            all_actions.append(ranged_action)

        # Spells (only if slot available)
        all_actions.extend(spell for spell in self.spells if self.spell_slots.has_slot(spell.level))

        # Special abilities (can have their own categories)
        all_actions += self.abilities

        return {action.id: action for action in all_actions if action.is_available(self.action_economy)}

    def __str__(self) -> str:
        return (
            f"**{self.name} {self.icon} (ID: {self.id})**\n\n"
            f"Class: {self.job.name} | Level: {self.level} | Party: {self.party.name}\n\n"
            f"HP: {self.attributes.hp}/{self.max_hp} | AC: {self.armor_class}\n\n"
            f"Position: ({self.pos.x}, {self.pos.y}) | Facing: {self.pos.direction} | "
            f"Movement Remaining: {self.current_speed}/{self.speed} m | Hidden: {self.is_hidden}\n\n"
            f"Status Effects: {', '.join(str(eff) for eff in self.status_effects) or 'None'}\n\n"
            f"Passives: {', '.join(eff.name for eff in self.passives) or 'None'}\n\n"
            f"Spell Slots: {self.spell_slots}\n\n"
            f"Stats: {Stats.model_validate(self.attributes.model_dump())}"
        )
