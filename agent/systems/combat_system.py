from agent.character.character import Character
from agent.character.stats import StatType
from agent.logs.events import EventType, Icon
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent

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

    def resolve_attack(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        roll = self.attack_roll(attack_stat=ctx.metadata["stat"], actor=actor, target=target)
        is_critical = roll.raw == actor.attributes.crit_roll()
        is_critical = is_critical or any(eff.is_auto_crit(actor, target) for eff in target.status_effects)

        ctx.hit_roll = roll
        ctx.is_critical = is_critical
        ctx.is_hit = is_critical or roll.total >= target.armor_class

        if ctx.is_critical:
            # Critical guarantees a hit -> direct damage roll with critical
            actor.log_event("Rolls a NATURAL 20! Critical hit!", icon=Icon.ROLL)
        else:
            # Check attack roll result
            actor.log_event(f"Attack roll: {roll.total} vs AC {target.armor_class}", icon=Icon.ROLL)
            if ctx.is_hit:
                actor.log_event("Attack roll passed → Hits target!", icon=Icon.ATTACK)
            else:
                actor.log_event("Attack roll failed → Target missed...", icon=Icon.ATTACK)
        return ctx.is_hit

    def resolve_save_throw(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        dc = actor.spell_save_dc
        stat: StatType = ctx.metadata["stat"]
        save_roll = self.save_roll(save_stat=stat, target=target, is_spell=True)

        ctx.hit_roll = save_roll
        ctx.is_hit = save_roll.total < dc

        actor.log_event(f"{stat.name} save: {save_roll.total} vs DC {dc}", icon=Icon.ROLL)

        if ctx.is_hit:
            actor.log_event("Save roll passed → Target resists!", icon=Icon.DEFENSE)
        else:
            actor.log_event("Save roll failed → Hits target!", icon=Icon.ATTACK)

        return ctx.is_hit

    def apply_damage(self, actor: Character, target: Character, ctx: CombatContext) -> CombatContext:
        # Damage roll
        mod = self._attack_modifier(actor, ctx)
        expr = f"{ctx.metadata['damage_dice']}+{mod}"
        droll = self.damage_roll(expr=expr, is_critical=ctx.is_critical)
        ctx.damage_roll = droll
        ctx.damage = Damage(components=[DamageComponent(value=droll.total, type=ctx.metadata["damage_type"])])
        actor.log_event(f"Damage roll: {droll.total}", icon=Icon.ROLL)

        # Apply actor status effects
        for effect in actor.status_effects:
            effect.on_apply_damage(actor, target, ctx)

        # Apply target resistances and vulnerabilities
        ctx.damage = target.modify_incoming_damage(ctx.damage)

        # Apply target status effects
        for effect in target.status_effects:
            effect.on_receive_damage(actor, target, ctx)

        # Apply damage
        total_damage = ctx.damage.total
        target.apply_damage(damage=total_damage)
        actor.log_event(f"Damage dealt: {total_damage} ({ctx.damage})", icon=Icon.DAMAGE)
        target.log_event(f"{target.name}: {target.attributes.hp}/{target.max_hp} HP")

        if not target.is_alive:
            target.log_event(f"{target.name} is defeated", icon=Icon.DEATH)
            return ctx

        return ctx

    def _attack_modifier(self, actor: Character, ctx: CombatContext) -> int:
        prof_bonus = actor.proficiency_bonus if ctx.metadata["weapon_type"] in actor.proficiencies else 0
        mod = actor.attributes.stat_modifier(ctx.metadata["stat"])
        return mod + prof_bonus
