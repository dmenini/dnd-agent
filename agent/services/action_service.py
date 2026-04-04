from typing import TYPE_CHECKING

from agent.actions.base import Action
from agent.actions.common.attack import MainHandAttackAction, OffHandAttackAction, RangedAttackAction
from agent.actions.common.dash import DashAction
from agent.actions.common.dodge import DodgeAction
from agent.actions.common.hide import HideAction
from agent.actions.common.move import MovementAction
from agent.actions.common.wait import WaitAction
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentType
from agent.equipment.weapons import MeleeWeapon
from agent.services.evocation_service import EvocationService

if TYPE_CHECKING:
    from agent.character.character import Character


class ActionService:
    """Stateless service for determining character action availability."""

    @classmethod
    def has_resources(cls, character: "Character") -> bool:
        """Check if character has any actions or movement remaining."""
        has_bonus = character.equipment.off_hand is not None and (character.action_economy.can_use_bonus())
        main_hand = character.equipment.main_hand or character.equipment.ranged or character.spells
        has_main = bool(main_hand) and character.action_economy.can_use_standard()
        # Technically we should check the speed left, but we force one movement per turn
        has_movement = character.action_economy.movement_available
        return has_main or has_bonus or has_movement

    @classmethod
    def can_use_spells(cls, character: "Character") -> bool:
        """Check if character can cast spells based on armor and proficiency.

        Can use spells if they are either wearing no armor or armor they are proficient with,
        or if their off-hand is empty or holding a shield they are proficient with.
        """
        return (
            not character.equipment.armor or character.attributes.has_proficiency(character.equipment.armor.armor_type)
        ) or (
            not character.equipment.off_hand
            or (
                character.equipment.off_hand.type == EquipmentType.SHIELD
                and character.attributes.has_proficiency(ArmorType.SHIELD)
            )
        )

    @classmethod
    def get_available_actions(cls, character: "Character") -> dict[str, Action]:
        """Get all actions currently available to the character."""
        all_actions: list[Action] = [
            MovementAction(range=character.current_speed),
            DashAction(range=character.current_speed),
            DodgeAction(),
            WaitAction(),
            HideAction(),
        ]

        # Equipment-based actions
        if character.equipment.main_hand:
            main_action = MainHandAttackAction.from_weapon(
                weapon=character.equipment.main_hand,
                is_two_handed=character.equipment.two_handed_active,
                abilities=character.attributes,
            )
            all_actions.append(main_action)
        if character.equipment.off_hand and isinstance(character.equipment.off_hand.type, MeleeWeapon):
            off_action = OffHandAttackAction.from_weapon(weapon=character.equipment.off_hand)
            all_actions.append(off_action)
        if character.equipment.ranged:
            ranged_action = RangedAttackAction.from_weapon(weapon=character.equipment.ranged)
            all_actions.append(ranged_action)

        # Spells (only if slot available and armor proficiency)
        if cls.can_use_spells(character):
            all_actions.extend(spell for spell in character.spells if character.spell_slots.has_slot(spell.level))

        # Special abilities (can have their own categories)
        all_actions += character.special_abilities

        # Actions from evocations (if any)
        all_actions += EvocationService.evocation_actions(character)

        return {action.id: action for action in all_actions if action.is_available(character.action_economy)}
