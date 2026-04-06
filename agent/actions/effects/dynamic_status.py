"""Dynamic status effect applicator with trait templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from agent.actions.effects.base import EffectApplicator
from agent.actions.expressions import ExpressionEvaluator
from agent.character.abilities import AbilityType
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.traits import TraitBuilder
from agent.logs.log_event import Icon
from agent.models.damage import DamageType
from agent.services.effect_service import EffectService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.effects.base import Trait
    from agent.models.context import CombatContext


class TraitTemplate(BaseModel):
    """Template for building a trait with dynamic values."""

    template_id: str = Field(description="Trait template identifier")
    params: dict[str, str | int | float] = Field(
        default_factory=dict, description="Parameters for the trait, can include expressions"
    )


class ApplyDynamicStatusEffect(EffectApplicator):
    """Apply a status effect with dynamically built traits.

    Used for:
    - Rage: builds traits with dynamic damage bonus
    - Haste: builds traits with various bonuses
    - Custom buffs/debuffs with variable strength
    """

    type: Literal["apply_dynamic_status"] = "apply_dynamic_status"
    status_type: StatusType
    duration: int | str = 1  # Can be expression
    save_dc: int = 0
    trait_templates: list[TraitTemplate] = Field(default_factory=list)

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Apply status effect with dynamically built traits."""
        # Evaluate duration
        duration = int(ExpressionEvaluator.eval(self.duration, actor, target, ctx))

        # Build traits from templates
        traits = []
        for template in self.trait_templates:
            trait = self._build_trait(template, actor, target, ctx)
            if trait:
                traits.append(trait)

        # Create and apply status effect
        effect = StatusEffect(
            type=self.status_type,
            duration=duration,
            save_dc=self.save_dc,
            traits=traits,
        )

        success = EffectService.try_apply_condition(target, effect)
        if success:
            actor.log_event(f"Applied {self.status_type.value} to {target.name}", icon=Icon.EFFECT_APPLIED)

    def _build_trait(
        self, template: TraitTemplate, actor: Character, target: Character, ctx: CombatContext
    ) -> Trait | None:
        """Build a trait from a template."""
        source_id = f"{self.status_type.value}_dynamic"

        # Evaluate all parameters
        params = {}
        for key, value in template.params.items():
            if isinstance(value, str):
                # Try to parse as enum or expression
                params[key] = self._eval_param(key, value, actor, target, ctx)
            else:
                params[key] = value

        # Build trait based on template_id
        template_id = template.template_id

        # Advantage/Disadvantage traits
        if template_id == "advantage_on_save":
            ability = params.get("ability")
            if isinstance(ability, str):
                ability = AbilityType(ability.lower())
            if not isinstance(ability, AbilityType):
                return None
            return TraitBuilder.advantage_on_save(source_id=source_id, ability=ability)

        if template_id == "advantage_on_attack":
            return TraitBuilder.attacker_advantage(source_id=source_id, name=self.status_type.value.title())

        # Resistance/Vulnerability
        if template_id == "resistance":
            damage_type = params.get("damage_type")
            if isinstance(damage_type, str):
                damage_type = DamageType(damage_type)
            if not isinstance(damage_type, DamageType):
                return None
            return TraitBuilder.resistance(source_id=source_id, damage_type=damage_type)

        if template_id == "vulnerability":
            damage_type = params.get("damage_type")
            if isinstance(damage_type, str):
                damage_type = DamageType(damage_type)
            if not isinstance(damage_type, DamageType):
                return None
            return TraitBuilder.vulnerability(source_id=source_id, damage_type=damage_type)

        # Damage bonuses
        if template_id == "melee_damage_bonus":
            value = params.get("value", 0)
            return TraitBuilder.melee_damage_bonus(source_id=source_id, value=int(value))

        if template_id == "weapon_damage_bonus":
            dice = params.get("dice", "1d4")
            damage_type = params.get("damage_type", DamageType.FORCE)
            if isinstance(damage_type, str):
                damage_type = DamageType(damage_type)
            return TraitBuilder.weapon_damage_bonus(
                source_id=source_id, name=self.status_type.value.title(), dice=str(dice), damage_type=damage_type
            )

        if template_id == "damage_bonus":
            value = params.get("value", 0)
            damage_type = params.get("damage_type", DamageType.FORCE)
            if isinstance(damage_type, str):
                damage_type = DamageType(damage_type.upper())
            return TraitBuilder.damage_bonus(
                source_id=source_id, name=self.status_type.value.title(), value=int(value), damage_type=damage_type
            )

        # AC bonuses
        if template_id == "ac_bonus":
            value = params.get("value", 0)
            return TraitBuilder.ac_bonus(source_id=source_id, name=self.status_type.value.title(), value=int(value))

        if template_id == "ac_bonus_with_armor":
            value = params.get("value", 0)
            return TraitBuilder.ac_bonus_with_armor(
                source_id=source_id, name=self.status_type.value.title(), value=int(value)
            )

        # Attack roll bonuses
        if template_id == "bonus_on_attack_roll":
            dice_expr = params.get("dice_expr", "1d4")
            return TraitBuilder.bonus_on_attack_roll(
                source_id=source_id, name=self.status_type.value.title(), dice_expr=str(dice_expr)
            )

        # Healing bonuses
        if template_id == "healing_bonus":
            value = params.get("value", 0)
            return TraitBuilder.healing_bonus(
                source_id=source_id, name=self.status_type.value.title(), value=int(value)
            )

        # Speed modifications
        if template_id == "speed_bonus":
            value = params.get("value", 0)
            return TraitBuilder.speed_bonus(source_id=source_id, name=self.status_type.value.title(), value=int(value))

        # Unknown template
        actor.log_event(f"Unknown trait template: {template_id}", icon=Icon.WARNING)
        return None

    def _eval_param(self, _: str, value: str, actor: Character, target: Character, ctx: CombatContext) -> Any:
        """Evaluate a parameter value."""
        try:
            return ExpressionEvaluator.eval(value, actor, target, ctx)
        except (TypeError, ValueError, SyntaxError):
            # Not an expression, return as string (likely an enum value)
            return value
