from logging import getLogger

from agent.mechanics.dice_roller import DiceRoller
from agent.models.character import Character
from agent.models.enums import COMBAT_ACTIONS
from agent.models.state import Action, ActionType, State

ATTACK_ROLL_EXPR = "1d20"

log = getLogger(__name__)


class CombatEngineNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        action = state.action
        actor = state.current_actor

        if not actor.is_alive:
            return state

        if not action:
            msg = f"No action for {actor.name}"
            raise ValueError(msg)

        target = state.characters.get(action.target_id) if action.target_id else None
        if not target:
            msg = f"No target for {action.action_type}"
            raise ValueError(msg)

        event = self._start_event_description(actor, action)

        # Handle the main combat actions
        if action.action_type in COMBAT_ACTIONS:
            event = self._resolve_combat_action(actor=actor, target=target, action=action, event=event)

        # Handle non-combat actions (move, wait, roleplay)
        elif action.action_type == ActionType.MOVE:
            event = event + " and moves strategically."

        elif action.action_type == ActionType.ROLEPLAY:
            event = event + " engages in roleplay."

        elif action.action_type == ActionType.WAIT:
            event = event + " and waits patiently."

        # Finalize turn
        state.append_log(event)
        return state

    def _start_event_description(self, actor: Character, action: Action) -> str:
        event = f"{actor.name} performs {action.action_type.value}"
        if action.description:
            event += f" ({action.description})"
        return event

    def _resolve_combat_action(
        self,
        actor: Character,
        target: Character,
        action: Action,
        event: str,
    ) -> str:
        """Handles attack/spell actions including criticals and damage."""
        weapon = actor.select_weapon(action_type=action.action_type)

        if not weapon:
            event += " but forgot to equip the weapon..."
            return event

        advantage = actor.stats.advantage(weapon.stat)

        # Attack roll determines hit/miss and crit
        roll = self.dice.roll_with_context(dice_expression=ATTACK_ROLL_EXPR, advantage=advantage)
        if roll.total < target.ac:
            event += " but misses..."
            return event

        is_critical = roll.raw == self.dice.sides(ATTACK_ROLL_EXPR)

        # 2nd roll determines damage dealt
        mod = actor.attack_modifier(weapon)
        expr = weapon.damage_dice + (f"+{mod}" if mod >= 0 else f"-{mod}")
        roll = self.dice.roll_with_context(dice_expression=expr, advantage=advantage)
        damage = roll.total

        if is_critical:
            event += " and rolls a NATURAL 20! Critical hit!"
            damage *= actor.crit_multiplier(weapon)
        else:
            event += f" and rolls {roll.total} to hit."

        # Apply damage
        target.apply_damage(damage=damage)
        event += f" Hits {target.name} for {damage} damage (HP now {target.attributes.current_hp})."

        if not target.is_alive:
            event += f" {target.name} is defeated!"

        return event
