from agent.character.character import Character
from agent.character.stats import StatType
from agent.logs.events import EventType
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller

D20 = "1d20"


class CombatSystem:
    def __init__(self, dice: DiceRoller) -> None:
        self._dice = dice

    def initiative_roll(self, actor: Character) -> DiceRoll:
        expr = f"{D20}+{actor.initiative_modifier}"
        roll = self._dice.roll_with_context(dice_expression=expr)
        actor.log_event(f"{actor.name} rolls initiative {roll.total}", event_type=EventType.MAIN)
        return roll

    def attack_roll(self, attack_stat: StatType, actor: Character, target: Character) -> DiceRoll:
        # Compute advantage from multiple sources
        sources = [
            actor.attributes.stat_advantage(attack_stat),
            actor.attributes.advantage("attack"),
            target.attributes.advantage("defense"),
        ]
        advantage = resolve_advantage(sources)

        return self._dice.roll_with_context(dice_expression=D20, advantage=advantage)

    def damage_roll(self, *, expr: str, is_critical: bool = False) -> DiceRoll:
        if is_critical:
            return self._dice.roll_twice(expr)
        return self._dice.roll_once(expr)

    def save_roll(self, save_stat: StatType, target: Character, *, is_spell: bool = False) -> DiceRoll:
        """
        Rolls a saving throw for the given ability type.
        Accounts for modifiers, proficiency, and active status effects.
        """
        if target.attributes.save_autofail(save_stat):
            return DiceRoll(expression=D20, rolls=[1], total=1, raw=1)

        # Compute advantage from multiple sources
        sources = [
            target.attributes.stat_advantage(save_stat),
            target.attributes.stat_save_advantage(save_stat),
        ]
        if is_spell:
            sources.append(target.attributes.spell_save_advantage())
        advantage = resolve_advantage(sources)

        # Roll the d20 (with advantage/disadvantage if applicable)
        ability_mod = target.attributes.stat_modifier(save_stat)
        prof_bonus = target.proficiency_bonus if save_stat in target.proficient_saves else 0
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"
        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)
