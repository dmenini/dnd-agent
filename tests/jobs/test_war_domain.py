import pytest

from agent.actions.base import ActionCategory, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.conditions import ApplyConditionsEffect
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.effects.trait_effects.support import guided_strike
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.cleric import Cleric, WarDomain
from agent.mechanics.dice_roller import DiceRoll
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType
from agent.services.effect_service import EffectService
from agent.services.job_service import JobService
from agent.services.level_service import LevelService


def test_war_domain_divine_favor(actor: Character) -> None:
    """Test that War Domain clerics learn Divine Favor spell."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Check that the cleric has Divine Favor
    spells = [a.id for a in actor.spells]
    assert FeatureId.DIVINE_FAVOR in spells

    # Find the Divine Favor spell
    divine_favor = next((s for s in actor.spells if s.id == FeatureId.DIVINE_FAVOR), None)
    assert divine_favor is not None
    assert divine_favor.name == "Divine Favor"

    # Check it's a bonus action
    assert divine_favor.category == ActionCategory.BONUS

    # Should be a ComposableAction
    assert isinstance(divine_favor, ComposableAction)

    # Check it applies the right condition
    apply_effect = next((e for e in divine_favor.effects if isinstance(e, ApplyConditionsEffect)), None)
    assert apply_effect is not None
    assert len(apply_effect.conditions) == 1
    condition = apply_effect.conditions[0]

    assert condition.type == StatusType.DIVINE_FAVORED

    # Check the condition has the weapon damage bonus trait
    assert len(condition.traits) == 1
    trait = condition.traits[0]
    assert trait.feature_id == FeatureId.WEAPON_DAMAGE_BONUS
    assert trait.effect_params["dice"] == "1d4"
    assert trait.effect_params["damage_type"] == DamageType.RADIANT


def test_war_domain_shield_of_faith(actor: Character, orc: Character) -> None:
    """Test that War Domain clerics learn Shield of Faith spell."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Check that the cleric has Shield of Faith
    spells = [a.id for a in actor.spells]
    assert FeatureId.SHIELD_OF_FAITH in spells

    # Find the Shield of Faith spell
    shield_of_faith = next((s for s in actor.spells if s.id == FeatureId.SHIELD_OF_FAITH), None)
    assert shield_of_faith is not None
    assert shield_of_faith.name == "Shield of Faith"

    # Check it's a bonus action
    assert shield_of_faith.category == ActionCategory.BONUS
    assert isinstance(shield_of_faith, ComposableAction)

    # Check it requires concentration
    apply_effect = next((e for e in shield_of_faith.effects if isinstance(e, ApplyConditionsEffect)), None)
    assert apply_effect is not None
    assert apply_effect.concentration

    # Check targeting and range
    assert shield_of_faith.targeting == TargetingType.SINGLE
    assert shield_of_faith.range == 60

    # Check the condition
    apply_effect = next((e for e in shield_of_faith.effects if isinstance(e, ApplyConditionsEffect)), None)
    assert apply_effect is not None
    assert len(apply_effect.conditions) == 1
    condition = apply_effect.conditions[0]
    assert condition.type == StatusType.SHIELDED_BY_FAITH
    assert condition.duration == 100  # 10 minutes

    # Check the AC bonus trait
    assert len(condition.traits) == 1
    trait = condition.traits[0]
    assert trait.feature_id == FeatureId.AC_BONUS
    # ModifierTrait has value directly, not in effect_params
    assert trait.value == 2

    # Test casting on an ally
    ctx = CombatContext()
    original_ac = orc.armor_class

    shield_of_faith.execute(actor, orc, ctx)

    # Caster should be concentrating
    assert actor.concentrating_on is not None
    assert actor.concentrating_on.type == StatusType.SHIELDED_BY_FAITH

    # Target should have the buff
    assert EffectService.has_condition(orc, StatusType.SHIELDED_BY_FAITH)
    assert orc.armor_class == original_ac + 2


def test_war_domain_guided_strike(actor: Character, orc: Character) -> None:
    """Test that War Domain clerics get Guided Strike at level 2."""
    # Start at level 1 before changing job
    actor.level = 1

    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # At level 1, should not have Guided Strike
    assert not any(p.feature_id == FeatureId.GUIDED_STRIKE for p in actor.passives)

    # Level up to 2
    LevelService.level_up(actor)
    assert actor.level == 2

    # Should now have Guided Strike passive
    assert any(p.feature_id == FeatureId.GUIDED_STRIKE for p in actor.passives)

    # Should have Channel Divinity uses
    channel_divinity = actor.get_resource("channel_divinity")
    assert channel_divinity.max_uses == 1
    assert channel_divinity.has_uses()

    # Test Guided Strike activation
    # Set up a scenario where attack would miss without bonus but hit with +10
    # AC is calculated from attributes.base_ac + armor.base_ac + dex + traits
    # We want: roll=15 misses, roll+10=25 hits, so AC should be between 16-25
    # Set base_ac to 0 and use armor to control the total AC precisely
    # With no base_ac: AC = armor.base_ac + dex + trait + 10 (if no armor type penalty)
    # Target AC ~20, so let's use heavy armor with base_ac 20 (no dex added)
    orc.attributes.base_ac = 0
    orc.equipment.armor = Armor(name="Plate", description="", armor_type=ArmorType.HEAVY, base_ac=20)
    target_ac = orc.armor_class

    ctx = CombatContext(enemies=[orc])

    # Mock an attack roll that would miss (total = 15)
    ctx.attack_roll = DiceRoll(expression="1d20+5", total=15, raw=10, advantage=None, rolls=[10])

    # Verify the conditions for Guided Strike
    assert target_ac > 15, f"Roll 15 should miss AC {target_ac}"
    assert target_ac <= 25, f"Roll 25 should hit AC {target_ac}"

    # Trigger the Guided Strike effect
    guided_strike(actor, orc, ctx)

    # Should have applied +10 bonus
    assert ctx.attack_roll.total == 25  # 15 + 10

    # Should have consumed Channel Divinity
    channel_divinity = actor.get_resource("channel_divinity")
    assert not channel_divinity.has_uses()
    assert channel_divinity.current_uses == 1


def test_guided_strike_not_used_if_already_hits(actor: Character, orc: Character) -> None:
    """Test that Guided Strike is not used if attack already hits."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    LevelService.level_up(actor)

    # Use orc fixture as target with low AC
    # AC is calculated from attributes.base_ac + armor.base_ac + dex + traits
    # Set base_ac very low and remove armor to get minimal AC
    orc.attributes.base_ac = 0
    orc.equipment.armor = None
    target_ac = orc.armor_class

    # Set up a scenario where attack already hits
    ctx = CombatContext(enemies=[orc])

    ctx.attack_roll = DiceRoll(expression="1d20+5", total=15, raw=10, advantage=None, rolls=[10])

    # Verify attack already hits
    assert target_ac <= 15, f"Roll 15 should hit AC {target_ac}"

    # Should not use Guided Strike
    guided_strike(actor, orc, ctx)

    # Should not have changed the roll
    assert ctx.attack_roll.total == 15

    # Should not have consumed Channel Divinity
    channel_divinity = actor.get_resource("channel_divinity")
    assert channel_divinity.has_uses()


def test_war_domain_heavy_armor_proficiency(actor: Character) -> None:
    """Test that War Domain clerics get heavy armor proficiency."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Should have heavy armor proficiency
    assert actor.attributes.has_proficiency(ArmorType.HEAVY)


def test_war_priest_feature(actor: Character, orc: Character) -> None:
    """Test that War Domain clerics get War Priest feature."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Check that the cleric has War Priest
    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.WAR_PRIEST in abilities

    # Find the War Priest action
    war_priest = next((a for a in actor.special_abilities if a.id == FeatureId.WAR_PRIEST), None)
    assert war_priest is not None
    assert isinstance(war_priest, ComposableAction)
    assert war_priest.name == "War Priest"

    # Check it's a bonus action
    assert war_priest.category == ActionCategory.BONUS
    assert war_priest.type == ActionType.ATTACK

    # ComposableAction uses resources for tracking uses, not uses_per_rest attribute
    # The resource tracking is configured in the job definition

    # Should not be available without using Attack action first
    assert not war_priest.is_available(actor.action_economy, actor)

    # Use Attack action
    actor.action_economy.use_standard(ActionType.ATTACK)

    # Now should be available
    assert war_priest.is_available(actor.action_economy, actor)

    # Execute the attack
    ctx = CombatContext()
    war_priest.execute(actor, orc, ctx)

    # Should consume one use
    war_priest.finalize(actor)
    war_priest_resource = actor.get_resource("war_priest")
    assert war_priest_resource.current_uses == 1

    # If we've used all available uses, should not be available even with Attack action
    if war_priest_resource.max_uses == 1:
        actor.action_economy.restore_turn()
        actor.action_economy.use_standard(ActionType.ATTACK)
        assert not war_priest.is_available(actor.action_economy, actor)

    # After rest, uses should be restored
    war_priest_resource.restore()
    assert war_priest_resource.current_uses == 0


def test_war_domain_magic_weapon(actor: Character, orc: Character) -> None:
    """Test that War Domain clerics learn Magic Weapon spell at level 3."""
    # Start at level 2 before changing job
    actor.level = 2

    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # At level 2, should not have Magic Weapon
    spells = [a.id for a in actor.spells]
    assert FeatureId.MAGIC_WEAPON not in spells

    # Level up to 3
    LevelService.level_up(actor)
    assert actor.level == 3

    # Should now have Magic Weapon
    spells = [a.id for a in actor.spells]
    assert FeatureId.MAGIC_WEAPON in spells

    # Find the Magic Weapon spell
    magic_weapon = next((s for s in actor.spells if s.id == FeatureId.MAGIC_WEAPON), None)
    assert magic_weapon is not None
    assert magic_weapon.name == "Magic Weapon"

    # Check it's a bonus action
    assert magic_weapon.category == ActionCategory.BONUS
    assert isinstance(magic_weapon, ComposableAction)

    # Check it requires concentration
    apply_effect = next((e for e in magic_weapon.effects if isinstance(e, ApplyConditionsEffect)), None)
    assert apply_effect is not None
    assert apply_effect.concentration

    # Check targeting and range
    assert magic_weapon.targeting == TargetingType.SINGLE
    assert magic_weapon.range == 1.5  # Touch range (1.5 squares)

    # Check the condition
    apply_effect = next((e for e in magic_weapon.effects if isinstance(e, ApplyConditionsEffect)), None)
    assert apply_effect is not None
    assert len(apply_effect.conditions) == 1
    condition = apply_effect.conditions[0]
    assert condition.type == StatusType.MAGIC_WEAPON
    assert condition.duration == 600  # 1 hour

    # Check the traits (attack bonus and damage bonus)
    assert len(condition.traits) == 2

    # Test casting on an ally
    ctx = CombatContext()

    magic_weapon.execute(actor, orc, ctx)

    # Caster should be concentrating
    assert actor.concentrating_on is not None
    assert actor.concentrating_on.type == StatusType.MAGIC_WEAPON

    # Target should have the buff
    assert EffectService.has_condition(orc, StatusType.MAGIC_WEAPON)


def test_war_domain_spiritual_weapon(actor: Character, orc: Character) -> None:
    """Test that War Domain clerics learn Spiritual Weapon spell at level 3."""

    # Skip this test - Spiritual Weapon needs evocation support which is pending
    pytest.skip("Spiritual Weapon requires evocation support - see task #12")

    # Start at level 2 before changing job
    actor.level = 2

    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # At level 2, should not have Spiritual Weapon
    spells = [a.id for a in actor.spells]
    assert FeatureId.SPIRITUAL_WEAPON not in spells

    # Level up to 3
    LevelService.level_up(actor)
    assert actor.level == 3

    # Should now have Spiritual Weapon
    spells = [a.id for a in actor.spells]
    assert FeatureId.SPIRITUAL_WEAPON in spells
