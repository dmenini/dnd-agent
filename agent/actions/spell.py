from __future__ import annotations

from typing import TYPE_CHECKING, Self

from agent.actions.attack import AttackAction
from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.equipment.weapons import WeaponType
from agent.logs.events import Icon
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent
from agent.models.enums import (
    TargetingType,
)

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.equipment.spells import AttackSpell, SupportSpell


class AttackSpellAction(AttackAction):
    id: str
    name: str
    description: str = ""
    action_type: ActionType = ActionType.CAST_SPELL
    category: ActionCategory = ActionCategory.STANDARD
    level: SpellLevel

    @classmethod
    def from_spell(cls, spell: AttackSpell) -> Self:
        return cls(
            id=f"cast_{spell.name.lower().replace(' ', '_')}",
            name=spell.name,
            description=f"Cast attack spell: {spell.description}",
            source=spell.name,
            action_type=ActionType.CAST_SPELL,
            weapon_type=WeaponType.MAGIC,
            category=spell.casting_time,
            targeting=spell.targeting,
            damage_dice=spell.damage_dice,
            damage_type=spell.damage_type,
            stat=spell.stat,
            range=spell.range,
            level=spell.level,
            status_effects=spell.effects,
        )

    def execute(self, actor: Character, target: Character) -> None:
        ctx = CombatContext()

        self._resolve_saving_throw(actor, target, ctx)

        # Apply damage if any
        if ctx.damage:
            self._apply_damage(actor, target, ctx)

    def _resolve_saving_throw(self, actor: Character, target: Character, ctx: CombatContext) -> CombatContext:
        dc = actor.spell_save_dc
        save_roll = target.save_roll(save_stat=self.stat, is_spell=True)

        ctx.hit_roll = save_roll
        ctx.is_hit = save_roll.total < dc

        actor.log_event(f"{self.stat.name} save: {save_roll.total} vs DC {dc}", icon=Icon.ROLL)

        if ctx.is_hit:
            actor.log_event(f"Save roll passed -> Target resists {self.name}!", icon=Icon.DEFENSE)
        else:
            actor.log_event("Save roll failed → Hits target!", icon=Icon.ATTACK)

            # Only apply damage if save failed
            mod = self._attack_modifier(actor)
            expr = f"{self.damage_dice}+{mod}"
            droll = actor.damage_roll(expr=expr, is_critical=False)
            ctx.damage_roll = droll
            ctx.damage = Damage(components=[DamageComponent(value=droll.total, type=self.damage_type)])
            actor.log_event(f"Damage roll: {droll.total}", icon=Icon.ROLL)

        return ctx

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)


class SupportSpellAction(Action):
    id: str
    name: str
    description: str = ""
    action_type: ActionType = ActionType.CAST_SPELL
    category: ActionCategory = ActionCategory.STANDARD
    level: SpellLevel
    source: str
    targeting: TargetingType
    stat: StatType
    range: float
    status_effects: list[StatusEffect] = []

    @classmethod
    def from_spell(cls, spell: SupportSpell) -> Self:
        return cls(
            id=f"cast_{spell.name.lower().replace(' ', '_')}",
            name=spell.name,
            description=f"Cast support spell: {spell.description}",
            source=spell.name,
            action_type=ActionType.CAST_SPELL,
            category=spell.casting_time,
            targeting=spell.targeting,
            stat=spell.stat,
            range=spell.range,
            level=spell.level,
            status_effects=spell.effects,
        )

    def execute(self, actor: Character, target: Character | None) -> None:
        if self.targeting == TargetingType.SELF:
            self._execute_on_target(target=actor)
        else:
            if target is None:
                raise ValueError
            self._execute_on_target(target=target)

    def _execute_on_target(self, target: Character) -> None:
        for effect in self.status_effects:
            target.try_apply_status(effect)

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)
