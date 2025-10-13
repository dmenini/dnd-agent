from logging import getLogger

from agent.mechanics.dice_roller import DiceRoller
from agent.models.action import COMBAT_ACTION_TYPES, ActionType
from agent.models.character import Character
from agent.models.state import Action, State

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

        event = self._start_event_description(actor, action)

        # Handle the main combat actions
        if action.action_type in COMBAT_ACTION_TYPES:
            if not action.target_ids:
                msg = f"No target(s) for action {action.id}"
                raise ValueError(msg)

            targets = [state.characters[tid] for tid in action.target_ids if tid in state.characters]
            if not targets:
                msg = f"Targets not found for action {action.id}"
                raise ValueError(msg)

            for target in targets:
                event = self._resolve_combat_action(
                    actor=actor,
                    target=target,
                    action=action,
                    event=event,
                )

        elif action.action_type == ActionType.DASH:
            event = self._resolve_movement_action(actor=actor, action=action, event=event)

        # Handle non-combat actions (move, wait, roleplay)
        elif action.action_type == ActionType.UTILITY:
            event += " performs a utility action."

        # Finalize turn
        state.append_log(event)
        return state

    def _start_event_description(self, actor: Character, action: Action) -> str:
        event = f"{actor.name} performs {action.name}"
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
        if not action or not action.damage_dice:
            raise ValueError

        advantage = actor.stats.advantage(action.stat)

        # Attack roll determines hit/miss and crit
        roll = self.dice.roll_with_context(dice_expression=ATTACK_ROLL_EXPR, advantage=advantage)
        if roll.total < target.ac:
            event += " but misses..."
            return event

        is_critical = roll.raw == self.dice.sides(ATTACK_ROLL_EXPR)

        # 2nd roll determines damage dealt
        mod = actor.attack_modifier(action)
        expr = action.damage_dice + (f"+{mod}" if mod >= 0 else f"-{mod}")
        roll = self.dice.roll_with_context(dice_expression=expr, advantage=advantage)

        if is_critical:
            damage = roll.raw * actor.crit_multiplier(action) + mod
            event += " and rolls a NATURAL 20! Critical hit!"
        else:
            damage = roll.total
            event += f" and rolls {roll.total} to hit."

        # Apply damage
        target.apply_damage(damage=damage)
        event += f" Hits {target.name} for {damage} damage (HP now {target.attributes.current_hp})."

        if not target.is_alive:
            event += f" {target.name} is defeated!"

        return event

    def _resolve_movement_action(self, actor: Character, action: Action, event: str) -> str:
        if not action.target_position:
            msg = "Movement requires a destination position"
            raise ValueError(msg)

        actor.move(action.target_position, dash=action.action_type == ActionType.DASH)
        event += f" and moves to position {action.target_position}."

        return event
