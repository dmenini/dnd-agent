from agent.mechanics.dice_roller import DiceRoller
from agent.models.character import Character, Weapon
from agent.models.state import Action, ActionType, State

ATTACK_ROLL_EXPR = "1d20"


class CombatEngineNode:
    def __init__(self, dice: DiceRoller) -> None:
        self.dice = dice

    def __call__(self, state: State) -> State:
        action = state.action
        actor = state.current_actor

        if not action:
            state.append_log(f"No action for {actor.name}")
            return state  # no action, skip

        target = state.characters.get(action.target_id) if action.target_id else None
        if not target:
            state.append_log(f"No target for {action.action_type}")
            return state  # no action, skip

        event = self._start_event_description(actor, action)

        # Handle the main combat actions
        if action.action_type in {ActionType.ATTACK, ActionType.SHOOT, ActionType.CAST_SPELL}:
            event = self._resolve_combat_action(actor=actor, target=target, action=action, event=event)

        # Handle non-combat actions (move, wait, roleplay)
        elif action.action_type in {ActionType.MOVE, ActionType.ROLEPLAY, ActionType.WAIT}:
            event = self._resolve_non_combat_action(action, event)

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
        weapon = self._select_weapon(character=actor, action_type=action.action_type)

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
        mod = actor.stats.modifier(weapon.stat)
        expr = weapon.damage_dice + (f"+{mod}" if mod >= 0 else f"-{mod}")
        roll = self.dice.roll_with_context(dice_expression=expr, advantage=advantage)
        damage = roll.total

        if is_critical:
            event += " and rolls a NATURAL 20! Critical hit!"
            damage *= actor.crit_multiplier
        else:
            event += f" and rolls {roll.total} to hit."

        # Apply damage
        self._apply_damage(target=target, damage=damage)
        event += f" Hits {target.name} for {damage} damage (HP now {max(0, target.hp)})."

        if target.hp <= 0:
            event += f" {target.name} is defeated!"

        return event

    def _select_weapon(self, character: Character, action_type: ActionType) -> Weapon | None:
        if action_type == ActionType.ATTACK:
            return character.melee_weapon
        if action_type == ActionType.CAST_SPELL:
            return character.spell
        if action_type == ActionType.SHOOT:
            return character.range_weapon
        return None

    def _apply_damage(self, target: Character, damage: int) -> None:
        target.hp = max(0, target.hp - damage)

    def _resolve_non_combat_action(self, action: Action, event: str) -> str:
        if action.action_type == ActionType.WAIT:
            return event + " and waits patiently."
        if action.action_type == ActionType.MOVE:
            return event + " and moves strategically."
        if action.action_type == ActionType.ROLEPLAY:
            return event + " engages in roleplay."
        return event
