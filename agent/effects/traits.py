from agent.character.abilities import AbilityType
from agent.character.proficiency import ProficiencyTarget
from agent.character.resources import ActionExtension
from agent.effects.base import ModifierTrait, Priority, Trait
from agent.effects.condition import Condition, When
from agent.equipment.armor import ArmorType
from agent.models.damage import DamageType
from agent.models.enums import EventType, FeatureId


class TraitBuilder:
    """Collection of builder functions for common trait patterns."""

    # ============================================================================
    # MODIFIER TRAITS - Direct attribute modifications
    # ============================================================================

    @staticmethod
    def attacker_disadvantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.ATTACKER_DISADVANTAGE,
            name=name,
            description=description or "Give disadvantage on attack roll to attacker.",
            attribute="disadvantage.defense",
            value=True,
            operation="set",
        )

    @staticmethod
    def attacker_advantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.ATTACKER_ADVANTAGE,
            name=name,
            description=description or "Give advantage on attack roll to attacker.",
            attribute="advantage.defense",
            value=True,
            operation="set",
        )

    @staticmethod
    def target_disadvantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.TARGET_DISADVANTAGE,
            name=name,
            description=description or "Give disadvantage on attack roll to target.",
            attribute="disadvantage.attack",
            value=True,
            operation="set",
        )

    @staticmethod
    def target_advantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.ATTACKER_ADVANTAGE,
            name=name,
            description=description or "Give advantage on attack roll to target.",
            attribute="advantage.attack",
            value=True,
            operation="set",
        )

    @staticmethod
    def disadvantage_on_save(
        source_id: str, ability: AbilityType, name: str = "", description: str = ""
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SAVE_DISADVANTAGE,
            name=name,
            description=description or f"Disadvantage on {ability.name} saving throws.",
            attribute=f"save_disadvantage.{ability.value}",
            value=True,
            operation="set",
        )

    @staticmethod
    def advantage_on_save(source_id: str, ability: AbilityType, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SAVE_ADVANTAGE,
            name=name,
            description=description or f"Advantage on {ability.name} saving throws.",
            attribute=f"save_advantage.{ability.value}",
            value=True,
            operation="set",
        )

    @staticmethod
    def autofail_save(source_id: str, ability: AbilityType, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SAVE_FAIL,
            name=name,
            description=description or f"Automatically fail {ability.name} saving throws.",
            attribute=f"save_autofail.{ability.value}",
            value=True,
            operation="set",
        )

    @staticmethod
    def speed_multiplier(source_id: str, value: float, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SPEED_MULTIPLIER,
            name=name,
            description=description or f"Multiply movement speed by {value}.",
            attribute="speed",
            value=value,
            operation="mul",
        )

    @staticmethod
    def speed_bonus(source_id: str, value: float, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SPEED_BONUS,
            name=name,
            description=description or f"Grant +{value} bonus to movement speed.",
            attribute="speed",
            value=value,
            operation="add",
        )

    @staticmethod
    def ac_bonus(
        source_id: str,
        value: int,
        conditions: list[Condition] | None = None,
        feature_id: FeatureId = FeatureId.AC_BONUS,
        name: str = "",
        description: str = "",
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=feature_id,
            name=name,
            description=description or description or f"Grant +{value} bonus to AC.",
            attribute="ac",
            value=value,
            operation="add",
            conditions=conditions or [],
        )

    @staticmethod
    def ac_bonus_with_armor(source_id: str, value: int = 1, name: str = "", description: str = "") -> ModifierTrait:
        return TraitBuilder.ac_bonus(
            source_id=source_id,
            feature_id=FeatureId.AC_BONUS_WITH_ARMOR,
            name=name,
            description=description or f"Grant +{value} bonus to AC while wearing armor.",
            value=value,
            conditions=[When.field("armor").exists()],
        )

    @staticmethod
    def ac_bonus_with_armor_types(
        source_id: str, armor_types: list[ArmorType], value: int = 1, name: str = "", description: str = ""
    ) -> ModifierTrait:
        armors = ", ".join(t.value for t in armor_types)
        return TraitBuilder.ac_bonus(
            source_id=source_id,
            feature_id=FeatureId.AC_BONUS_WITH_ARMOR_TYPES,
            name=name,
            description=description or f"Grant +{value} bonus to AC with {armors} armor.",
            value=value,
            conditions=[When.field("armor.armor_type").is_in(armor_types)],
        )

    @staticmethod
    def ac_bonus_without_armor(source_id: str, value: int = 3, name: str = "", description: str = "") -> ModifierTrait:
        return TraitBuilder.ac_bonus(
            source_id=source_id,
            feature_id=FeatureId.AC_BONUS_WITHOUT_ARMOR,
            name=name,
            description=description or f"Grant +{value} bonus to AC while not wearing armor.",
            value=value,
            conditions=[When.field("armor").is_falsy()],
        )

    @staticmethod
    def ac_mod_bonus_without_armor(
        source_id: str, ability: AbilityType = AbilityType.CON, name: str = "", description: str = ""
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.AC_BONUS_MOD_WITHOUT_ARMOR,
            name=name,
            description=description or f"Add {ability.name} modifier to AC without armor.",
            attribute=f"ac_mod.{ability.value}",
            value=True,
            conditions=[When.field("armor").is_falsy()],
        )

    @staticmethod
    def critical_roll_bonus(source_id: str, value: int, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.CRITICAL_ROLL_BONUS,
            name=name,
            description=description or f"Critical hits occur {value} points earlier (e.g., on {20 - value}).",
            attribute="crit_roll_bonus",
            value=value,
            operation="add",
        )

    @staticmethod
    def resistance(
        source_id: str, damage_type: DamageType, value: float = 0.5, name: str = "", description: str = ""
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.RESISTANCE,
            name=name,
            description=description or f"Gain {value:.0%} resistance to {damage_type.value} damage.",
            attribute=f"resistance.{damage_type.value}",
            value=value,
            operation="add",
        )

    @staticmethod
    def immunity(source_id: str, damage_type: DamageType, name: str = "", description: str = "") -> ModifierTrait:
        return TraitBuilder.resistance(
            source_id=source_id,
            name=name,
            description=description,
            damage_type=damage_type,
            value=1.0,
        )

    @staticmethod
    def vulnerability(
        source_id: str, damage_type: DamageType, value: float = 0.5, name: str = "", description: str = ""
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.VULNERABILITY,
            name=name,
            description=description or f"Take {value:.0%} additional {damage_type.value} damage.",
            attribute=f"vulnerability.{damage_type.value}",
            value=value,
            operation="add",
        )

    @staticmethod
    def spell_resistance(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SPELL_SAVE_ADVANTAGE,
            name=name,
            description=description or "Advantage on saving throws against spells.",
            attribute="save_advantage.spell",
            value=True,
            operation="set",
        )

    @staticmethod
    def spell_weakness(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.SPELL_SAVE_DISADVANTAGE,
            name=name,
            description=description or "Disadvantage on saving throws against spells.",
            attribute="save_disadvantage.spell",
            value=True,
            operation="set",
        )

    @staticmethod
    def stealth_advantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.STEALTH_ADVANTAGE,
            name=name,
            description=description or "Advantage on Stealth checks.",
            attribute="advantage.stealth",
            value=True,
            operation="set",
        )

    @staticmethod
    def stealth_disadvantage(source_id: str, name: str = "", description: str = "") -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.STEALTH_DISADVANTAGE,
            name=name,
            description=description or "Disadvantage on Stealth checks.",
            attribute="disadvantage.stealth",
            value=True,
            operation="set",
        )

    @staticmethod
    def expertise(
        source_id: str, proficiency: ProficiencyTarget, name: str = "", description: str = ""
    ) -> ModifierTrait:
        return ModifierTrait(
            source_id=source_id,
            feature_id=FeatureId.EXPERTISE,
            name=name,
            description=description or f"Gain expertise with {proficiency.value}.",
            attribute=f"expertise.{proficiency.value}",
            value=True,
            operation="set",
        )

    # ============================================================================
    # EVENT TRAITS - Callback-based effects
    # ============================================================================

    @staticmethod
    def auto_crit_if_melee(
        source_id: str, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """Give automatic critical hits when in melee range."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.AUTO_CRIT_IF_MELEE,
            name=name or "Auto-Crit (Melee)",
            description=description or "Automatically score critical hits against targets within melee range.",
            event_type=EventType.COMBAT_START,
            effect_type="auto_crit_if_melee",
            conditions=conditions or [],
        )

    @staticmethod
    def cannot_move(
        source_id: str, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """The target cannot move during its turn."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.CANNOT_MOVE,
            name=name or "Cannot Move",
            description=description or "Movement speed is reduced to 0.",
            event_type=EventType.TURN_START,
            conditions=conditions or [],
        )

    @staticmethod
    def cannot_act(
        source_id: str, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """The target cannot take any actions during its turn."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.CANNOT_ACT,
            name=name or "Incapacitated",
            description=description or "Cannot take actions, bonus actions, or reactions.",
            event_type=EventType.TURN_START,
            conditions=conditions or [],
        )

    @staticmethod
    def extra_actions(
        source_id: str,
        extensions: list[ActionExtension],
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Grant additional actions to the target at the start of its turn."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.EXTRA_ACTIONS,
            name=name or "Extra Actions",
            description=description or f"Gain {len(extensions)} additional action(s).",
            event_type=EventType.TURN_START,
            effect_params={"extensions": extensions},
            conditions=conditions or [],
            priority=50,
        )

    @staticmethod
    def half_attacks(
        source_id: str, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """Reduce number of attack-type extra actions by half."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.HALF_ATTACKS,
            name=name or "Reduced Attacks",
            description=description or "Number of attacks is halved.",
            event_type=EventType.TURN_START,
            effect_type="half_attacks",
            conditions=conditions or [],
            priority=Priority.LOW,  # Apply after extra actions are added
        )

    @staticmethod
    def bonus_on_attack_roll(
        source_id: str,
        dice_expr: str = "1d4",
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """The target can roll a bonus die and add it to the attack roll."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.ATTACK_ROLL_BONUS,
            name=name or f"Attack Bonus ({dice_expr})",
            description=description or f"Roll {dice_expr} and add to attack rolls.",
            event_type=EventType.ATTACK_ROLL,
            effect_params={"expr": dice_expr},
            conditions=conditions or [],
        )

    @staticmethod
    def bonus_on_save_throw(
        source_id: str,
        dice_expr: str = "1d4",
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """The target can roll a bonus die and add it to the save throw."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.SAVE_ROLL_BONUS,
            name=name or f"Save Bonus ({dice_expr})",
            description=description or f"Roll {dice_expr} and add to saving throws.",
            event_type=EventType.SAVE_THROW,
            effect_type="bonus_save_roll",
            effect_params={"expr": dice_expr},
            conditions=conditions or [],
        )

    @staticmethod
    def reflect_melee_damage(
        source_id: str,
        ratio: float = 0.1,
        damage_type: DamageType = DamageType.FORCE,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Reflect a portion of melee damage received back to the attacker."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.REFLECT_MELEE_DAMAGE,
            name=name or "Damage Reflection",
            description=description or f"Reflect {ratio:.0%} of melee damage as {damage_type.value}.",
            event_type=EventType.RECEIVE_DAMAGE,
            effect_params={"ratio": ratio, "damage_type": damage_type.value},
            conditions=conditions or [],
            priority=Priority.LOW,  # Apply after damage is calculated
        )

    @staticmethod
    def life_steal(
        source_id: str,
        ratio: float = 0.1,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Heal the attacker by a portion of the damage they deal."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.LIFE_STEAL,
            name=name,
            description=description or f"Heal for {ratio:.0%} of damage dealt.",
            event_type=EventType.APPLY_DAMAGE,
            effect_params={"ratio": ratio},
            conditions=conditions or [],
            priority=Priority.LOW,  # Apply after damage is calculated
        )

    @staticmethod
    def damage_bonus(
        source_id: str,
        value: int,
        damage_type: DamageType,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Add bonus damage of a given type to all damage dealt."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.DAMAGE_BONUS,
            name=name,
            description=description or f"Deal an additional {value} {damage_type.value} damage.",
            event_type=EventType.APPLY_DAMAGE,
            effect_type="damage_bonus",
            effect_params={"value": value, "damage_type": damage_type.value},
            conditions=conditions or [],
        )

    @staticmethod
    def melee_damage_bonus(
        source_id: str, value: int, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """Add bonus damage for melee weapon attacks using Strength."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.DAMAGE_BONUS_WITH_MELEE_WEAPON,
            name=name,
            description=description or f"Deal +{value} damage with melee Strength attacks.",
            event_type=EventType.APPLY_DAMAGE,
            effect_params={"value": value},
            conditions=conditions or [],
        )

    @staticmethod
    def sneak_attack(
        source_id: str, dice_expr: str, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """Add sneak attack damage when attacking with advantage."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE,
            name=name,
            description=description or f"Deal {dice_expr} extra damage with advantage (once per turn).",
            event_type=EventType.APPLY_DAMAGE,
            effect_params={"dice": dice_expr},
            conditions=conditions or [],
        )

    @staticmethod
    def damage_multiplier(
        source_id: str,
        value: float,
        damage_type: DamageType,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Multiply damage of a specific type by a given factor."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.DAMAGE_MULTIPLIER,
            name=name or f"{damage_type.value.title()} Damage x{value}",
            description=description or f"Multiply {damage_type.value} damage by {value}.",
            event_type=EventType.APPLY_DAMAGE,
            effect_type="damage_multiplier",
            effect_params={"value": value, "damage_type": damage_type.value},
            conditions=conditions or [],
        )

    @staticmethod
    def ignore_resistance(
        source_id: str,
        damage_type: DamageType,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Negate the target's resistance to a specific damage type."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.IGNORE_RESISTANCE,
            name=name or f"Ignore {damage_type.value.title()} Resistance",
            description=description or f"Your attacks ignore {damage_type.value} resistance.",
            event_type=EventType.APPLY_DAMAGE,
            effect_type="ignore_resistance",
            effect_params={"damage_type": damage_type.value},
            conditions=conditions or [],
            priority=Priority.LOW,  # Needs to apply after resistance calculation
        )

    @staticmethod
    def regeneration(
        source_id: str, value: int, conditions: list[Condition] | None = None, name: str = "", description: str = ""
    ) -> Trait:
        """Heal target by the given amount every turn."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.REGENERATION,
            name=name,
            description=description or f"Heal {value} HP at the start of each turn.",
            event_type=EventType.TURN_START,
            effect_params={"value": value},
            conditions=conditions or [],
        )

    @staticmethod
    def damage_over_time(
        source_id: str,
        value: int,
        damage_type: DamageType,
        conditions: list[Condition] | None = None,
        name: str = "",
        description: str = "",
    ) -> Trait:
        """Deal damage at the end of each turn."""
        return Trait(
            source_id=source_id,
            feature_id=FeatureId.DAMAGE_OVER_TIME,
            name=name or f"{damage_type.value.title()} Damage Over Time",
            description=description or f"Take {value} {damage_type.value} damage at turn end.",
            event_type=EventType.TURN_END,
            effect_type="damage_over_time",
            effect_params={"value": value, "damage_type": damage_type.value},
            conditions=conditions or [],
            priority=Priority.HIGH,
        )
