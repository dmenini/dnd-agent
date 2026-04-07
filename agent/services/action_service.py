from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionType
from agent.actions.common.dash import DashAction
from agent.actions.common.dodge import DodgeAction
from agent.actions.common.hide import HideAction
from agent.actions.common.move import MovementAction
from agent.actions.common.wait import WaitAction
from agent.actions.composable import ComposableAction
from agent.actions.effects.conditions import ApplyConditionsEffect
from agent.actions.effects.damage import DamageEffect
from agent.actions.resources import SpellSlotConsumer
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.character.abilities import AbilityType
from agent.character.attributes import Attributes
from agent.character.resources import SpellLevel
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentType
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling
from agent.services.evocation_service import EvocationService

if TYPE_CHECKING:
    from agent.character.character import Character


class ActionService:
    """Stateless service for determining character action availability."""

    @staticmethod
    def weapon_to_action(
        weapon: MeleeWeapon | RangedWeapon,
        action_id: str,
        name: str,
        category: ActionCategory,
        action_type: ActionType,
        *,
        is_two_handed: bool = False,
        abilities: Attributes | None = None,
    ) -> ComposableAction:
        """Build a ComposableAction from weapon data.

        Args:
            weapon: The weapon to build an action from
            action_id: Unique ID for the action
            name: Display name
            category: STANDARD or BONUS
            action_type: ATTACK or OFF_HAND_ATTACK
            is_two_handed: Whether wielding two-handed (for versatile weapons)
            abilities: Character abilities (for finesse weapon ability selection)

        Returns:
            ComposableAction configured for this weapon attack
        """
        # Determine damage dice (versatile weapons deal more damage two-handed)
        damage_dice = weapon.damage_dice
        if isinstance(weapon, MeleeWeapon) and weapon.handling == WeaponHandling.VERSATILE and is_two_handed:
            damage_dice = weapon.versatile_damage or damage_dice

        # Determine ability (finesse weapons can use STR or DEX, player chooses best)
        ability = weapon.ability
        if isinstance(weapon, MeleeWeapon) and weapon.finesse and abilities:
            ability = AbilityType.STR if abilities.strength >= abilities.dexterity else AbilityType.DEX

        # Build effects list: damage first, then weapon effects (if any)
        action_effects: list = [
            DamageEffect(
                damage_dice=damage_dice,
                damage_type=weapon.damage_type,
                ability=ability,
            )
        ]
        if weapon.effects:
            action_effects.append(ApplyConditionsEffect(conditions=weapon.effects))

        return ComposableAction(
            id=action_id,
            name=name,
            description=f"Attack with {weapon.name}",
            type=action_type,
            category=category,
            targeting=weapon.targeting,
            range=weapon.range,
            hits=1,
            resolution=AttackRollStrategy(
                ability=ability,
                weapon_type=weapon.weapon_type,
            ),
            effects=action_effects,
            resources=[
                ActionEconomyConsumer(
                    category=category,
                    action_type=action_type,
                )
            ],
            metadata={"weapon": weapon.name},
        )

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
    def _has_spell_slot(cls, character: "Character", spell: Action) -> bool:
        """Check if character has spell slot for the given spell action.

        Handles both old-style spell actions (with .level attribute) and
        ComposableActions (with SpellSlotConsumer in .resources).
        """
        # For ComposableAction, check resources for SpellSlotConsumer
        if isinstance(spell, ComposableAction):
            for resource in spell.resources:
                if isinstance(resource, SpellSlotConsumer):
                    return resource.is_available(character)
            # No spell slot consumer means it doesn't require a slot (shouldn't happen for spells)
            return True

        # For old-style spell actions, use .level attribute
        if hasattr(spell, "level") and isinstance(spell.level, SpellLevel):
            return character.spell_slots.has_slot(spell.level)

        # Fallback: if we can't determine, assume available
        return True

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

        # Equipment-based actions (weapon attacks built from weapon data)
        if character.equipment.main_hand:
            main_action = cls.weapon_to_action(
                weapon=character.equipment.main_hand,
                action_id="main_hand_attack",
                name="Main Hand Attack",
                category=ActionCategory.STANDARD,
                action_type=ActionType.ATTACK,
                is_two_handed=character.equipment.two_handed_active,
                abilities=character.attributes,
            )
            all_actions.append(main_action)
        if character.equipment.off_hand and isinstance(character.equipment.off_hand, MeleeWeapon):
            off_action = cls.weapon_to_action(
                weapon=character.equipment.off_hand,
                action_id="off_hand_attack",
                name="Off Hand Attack",
                category=ActionCategory.BONUS,
                action_type=ActionType.OFF_HAND_ATTACK,
            )
            all_actions.append(off_action)
        if character.equipment.ranged:
            ranged_action = cls.weapon_to_action(
                weapon=character.equipment.ranged,
                action_id="ranged_attack",
                name="Ranged Attack",
                category=ActionCategory.STANDARD,
                action_type=ActionType.ATTACK,
            )
            all_actions.append(ranged_action)

        # Spells (only if slot available and armor proficiency)
        if cls.can_use_spells(character):
            all_actions.extend(spell for spell in character.spells if cls._has_spell_slot(character, spell))

        # Special abilities (can have their own categories)
        all_actions += character.special_abilities

        # Actions from evocations (if any)
        all_actions += EvocationService.evocation_actions(character)

        return {action.id: action for action in all_actions if action.is_available(character.action_economy)}
