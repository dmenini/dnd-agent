from agent.actions.base import ActionCategory, ActionType
from agent.character.abilities import AbilityType
from agent.character.resources import ActionExtension
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.traits import TraitBuilder
from agent.models.damage import DamageType

Blessed = StatusEffect(
    type=StatusType.BLESSED,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.bonus_on_attack_roll(source_id=StatusType.BLESSED.value, dice_expr="1d4"),
        TraitBuilder.bonus_on_save_throw(source_id=StatusType.BLESSED.value, dice_expr="1d4"),
    ],
    duration=1,
)

Dodge = StatusEffect(
    type=StatusType.DODGING,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.attacker_disadvantage(source_id=StatusType.DODGING.value),
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
    type=StatusType.HASTED,
    save_dc=0,  # Skip save throw as it's cast on a willing creature
    traits=[
        TraitBuilder.extra_actions(source_id=StatusType.HASTED.value, extensions=[StandardActionExtension]),
        TraitBuilder.speed_multiplier(source_id=StatusType.HASTED.value, value=2),
        TraitBuilder.ac_bonus(source_id=StatusType.HASTED.value, value=2),
        TraitBuilder.advantage_on_save(source_id=StatusType.HASTED.value, ability=AbilityType.DEX),
    ],
    duration=10,
    followup=None,  # Will be resolved after Lethargic is defined
)

Lethargic = StatusEffect(
    type=StatusType.LETHARGIC,
    save_dc=10,
    save_ability=AbilityType.WIS,
    save_mode="start",
    traits=[
        TraitBuilder.speed_multiplier(source_id=StatusType.LETHARGIC.value, value=0.5),
        TraitBuilder.disadvantage_on_save(source_id=StatusType.LETHARGIC.value, ability=AbilityType.WIS),
        TraitBuilder.half_attacks(source_id=StatusType.LETHARGIC.value),
    ],
    duration=1,
)

# Update Hasted's followup now that Lethargic is defined
Hasted.followup = Lethargic.with_duration(1)

Paralyzed = StatusEffect(
    type=StatusType.PARALYZED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_act(source_id=StatusType.PARALYZED.value),
        TraitBuilder.cannot_move(source_id=StatusType.PARALYZED.value),
        TraitBuilder.attacker_advantage(source_id=StatusType.PARALYZED.value),
        TraitBuilder.auto_crit_if_melee(source_id=StatusType.PARALYZED.value),
        TraitBuilder.autofail_save(source_id=StatusType.PARALYZED.value, ability=AbilityType.STR),
        TraitBuilder.autofail_save(source_id=StatusType.PARALYZED.value, ability=AbilityType.DEX),
    ],
    duration=1,
)

Poisoned = StatusEffect(
    type=StatusType.POISONED,
    save_dc=10,
    traits=[
        TraitBuilder.target_disadvantage(source_id=StatusType.POISONED.value),
        TraitBuilder.damage_over_time(source_id=StatusType.POISONED.value, value=1, damage_type=DamageType.POISON),
    ],
    duration=1,
)

Restrained = StatusEffect(
    type=StatusType.RESTRAINED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_move(source_id=StatusType.RESTRAINED.value),
        TraitBuilder.disadvantage_on_save(source_id=StatusType.RESTRAINED.value, ability=AbilityType.DEX),
        TraitBuilder.attacker_advantage(source_id=StatusType.RESTRAINED.value),
        TraitBuilder.target_disadvantage(source_id=StatusType.RESTRAINED.value),
    ],
    duration=1,
)

Stunned = StatusEffect(
    type=StatusType.STUNNED,
    save_dc=10,
    traits=[
        TraitBuilder.cannot_act(source_id=StatusType.STUNNED.value),
        TraitBuilder.cannot_move(source_id=StatusType.STUNNED.value),
        TraitBuilder.attacker_advantage(source_id=StatusType.STUNNED.value),
        TraitBuilder.autofail_save(source_id=StatusType.STUNNED.value, ability=AbilityType.STR),
        TraitBuilder.autofail_save(source_id=StatusType.STUNNED.value, ability=AbilityType.DEX),
    ],
    duration=1,
)

DivineFavored = StatusEffect(
    type=StatusType.DIVINE_FAVORED,
    save_dc=0,
    traits=[
        TraitBuilder.weapon_damage_bonus(
            source_id=StatusType.DIVINE_FAVORED.value,
            name="Divine Favor",
            dice="1d4",
            damage_type=DamageType.RADIANT,
        )
    ],
    duration=10,
)

MagicWeapon = StatusEffect(
    type=StatusType.MAGIC_WEAPON,
    save_dc=0,
    traits=[
        TraitBuilder.bonus_on_attack_roll(
            source_id=StatusType.MAGIC_WEAPON.value,
            name="Magic Weapon",
            dice_expr="1",
        ),
        TraitBuilder.damage_bonus(
            source_id=StatusType.MAGIC_WEAPON.value,
            name="Magic Weapon",
            value=1,
            damage_type=DamageType.FORCE,
        ),
    ],
    duration=600,
)

ShieldedByFaith = StatusEffect(
    type=StatusType.SHIELDED_BY_FAITH,
    save_dc=0,
    traits=[
        TraitBuilder.ac_bonus(
            source_id=StatusType.SHIELDED_BY_FAITH.value,
            name="Shield of Faith",
            value=2,
        )
    ],
    duration=100,
)
