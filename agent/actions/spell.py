from __future__ import annotations

from typing import TYPE_CHECKING, Self

from agent.actions.attack import AttackAction
from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.equipment.weapons import WeaponType
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
    action_type: ActionType = ActionType.SPELL
    category: ActionCategory = ActionCategory.STANDARD
    level: SpellLevel

    @classmethod
    def from_spell(cls, spell: AttackSpell) -> Self:
        return cls(
            id=f"cast_{spell.name.lower().replace(' ', '_')}",
            name=spell.name,
            description=f"Cast attack spell: {spell.description}",
            source=spell.name,
            action_type=ActionType.SPELL,
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

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)


class SupportSpellAction(Action):
    id: str
    name: str
    description: str = ""
    action_type: ActionType = ActionType.SPELL
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
            action_type=ActionType.SPELL,
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

    def _execute_on_target(self, target: Character) -> str:
        event = ""
        for effect in self.status_effects:
            affected = target.try_apply_status(effect)
            if affected:
                event += f" {target.name} is {effect.type.value}."
        return event

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)
