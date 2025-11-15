from agent.actions.base import ActionCategory, ActionType
from agent.character.abilities import AbilityType
from agent.character.collection import ActionExtension
from agent.effects.status_effects.base import EffectType, StatusEffect
from agent.effects.traits import TraitBuilder
from agent.models.damage import DamageType

Blessed = StatusEffect(
    type=EffectType.BLESSED,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.bonus_on_attack_roll(source_id=EffectType.BLESSED.value, dice_expr="1d4"),
        TraitBuilder.bonus_on_save_throw(source_id=EffectType.BLESSED.value, dice_expr="1d4"),
    ],
    duration=1,
)

Dodge = StatusEffect(
    type=EffectType.DODGING,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.attacker_disadvantage(source_id=EffectType.DODGING.value),
    ],
    duration=1,
)

StandardActionExtension = ActionExtension(
    source="haste",
    category=ActionCategory.STANDARD,
    allowed_actions=[
        ActionType.ATTACK,  # TODO: Limit to 1 hand attack or ranged
        ActionType.DASH,
        ActionType.DISENGAGE,
        ActionType.HIDE,
        ActionType.USE_OBJECT,
    ],
    requires_previous_action=True,
    expires_end_of_turn=True,
)

Hasted = StatusEffect(
    type=EffectType.HASTED,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.extra_actions(source_id=EffectType.HASTED.value, extensions=[StandardActionExtension]),
        TraitBuilder.speed_multiplier(source_id=EffectType.HASTED.value, value=2),
        TraitBuilder.ac_bonus(source_id=EffectType.HASTED.value, value=2),
        TraitBuilder.advantage_on_save(source_id=EffectType.HASTED.value, ability=AbilityType.DEX),
    ],
    duration=10,
    followup=None,  # Will be resolved after Lethargic is defined
)

Lethargic = StatusEffect(
    type=EffectType.LETHARGIC,
    save_dc=10,
    save_ability=AbilityType.WIS,
    save_mode="start",
    traits=[
        TraitBuilder.speed_multiplier(source_id=EffectType.LETHARGIC.value, value=0.5),
        TraitBuilder.disadvantage_on_save(source_id=EffectType.LETHARGIC.value, ability=AbilityType.WIS),
        TraitBuilder.half_attacks(source_id=EffectType.LETHARGIC.value),
    ],
    duration=1,
)

# Update Hasted's followup now that Lethargic is defined
Hasted.followup = Lethargic.with_duration(1)

Paralyzed = StatusEffect(
    type=EffectType.PARALYZED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_act(source_id=EffectType.PARALYZED.value),
        TraitBuilder.cannot_move(source_id=EffectType.PARALYZED.value),
        TraitBuilder.attacker_advantage(source_id=EffectType.PARALYZED.value),
        TraitBuilder.auto_crit_if_melee(source_id=EffectType.PARALYZED.value),
        TraitBuilder.autofail_save(source_id=EffectType.PARALYZED.value, ability=AbilityType.STR),
        TraitBuilder.autofail_save(source_id=EffectType.PARALYZED.value, ability=AbilityType.DEX),
    ],
    duration=1,
)

Poisoned = StatusEffect(
    type=EffectType.POISONED,
    save_dc=10,
    traits=[
        TraitBuilder.target_disadvantage(source_id=EffectType.POISONED.value),
        TraitBuilder.damage_over_time(source_id=EffectType.POISONED.value, value=1, damage_type=DamageType.POISON),
    ],
    duration=1,
)

Restrained = StatusEffect(
    type=EffectType.RESTRAINED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_move(source_id=EffectType.RESTRAINED.value),
        TraitBuilder.disadvantage_on_save(source_id=EffectType.RESTRAINED.value, ability=AbilityType.DEX),
        TraitBuilder.attacker_advantage(source_id=EffectType.RESTRAINED.value),
        TraitBuilder.target_disadvantage(source_id=EffectType.RESTRAINED.value),
    ],
    duration=1,
)

Stunned = StatusEffect(
    type=EffectType.STUNNED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_act(source_id=EffectType.STUNNED.value),
        TraitBuilder.cannot_move(source_id=EffectType.STUNNED.value),
        TraitBuilder.attacker_advantage(source_id=EffectType.STUNNED.value),
        TraitBuilder.autofail_save(source_id=EffectType.STUNNED.value, ability=AbilityType.STR),
        TraitBuilder.autofail_save(source_id=EffectType.STUNNED.value, ability=AbilityType.DEX),
    ],
    duration=1,
)
