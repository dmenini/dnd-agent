from agent.actions.base import ActionCategory, ActionType
from agent.actions.common.spell import BonusSupportSpellAction
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.equipment.armor import ArmorType
from agent.jobs.cleric import Cleric, WarDomain
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType
from agent.services.effect_service import EffectService
from agent.services.job_service import JobService


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

    # Narrow the type to BonusSupportSpellAction
    assert isinstance(divine_favor, BonusSupportSpellAction)

    # Check it applies the right condition
    assert len(divine_favor.apply_conditions) == 1
    condition = divine_favor.apply_conditions[0]

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
    assert isinstance(shield_of_faith, BonusSupportSpellAction)

    # Check it requires concentration
    assert shield_of_faith.requires_concentration

    # Check targeting and range
    assert shield_of_faith.targeting == TargetingType.SINGLE
    assert shield_of_faith.range == 60

    # Check the condition
    assert len(shield_of_faith.apply_conditions) == 1
    condition = shield_of_faith.apply_conditions[0]
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
    from agent.services.level_service import LevelService  # noqa: PLC0415

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
    from agent.equipment.armor import Armor, ArmorType  # noqa: PLC0415

    orc.equipment.armor = Armor(name="Plate", description="", armor_type=ArmorType.HEAVY, base_ac=20)
    target_ac = orc.armor_class

    ctx = CombatContext(enemies=[orc])

    # Mock an attack roll that would miss (total = 15)
    from agent.mechanics.dice_roller import DiceRoll  # noqa: PLC0415

    ctx.attack_roll = DiceRoll(expression="1d20+5", total=15, raw=10, advantage=None, rolls=[10])

    # Verify the conditions for Guided Strike
    assert target_ac > 15, f"Roll 15 should miss AC {target_ac}"
    assert target_ac <= 25, f"Roll 25 should hit AC {target_ac}"

    # Trigger the Guided Strike effect
    from agent.effects.trait_effects.support import guided_strike  # noqa: PLC0415

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

    from agent.services.level_service import LevelService  # noqa: PLC0415

    LevelService.level_up(actor)

    # Use orc fixture as target with low AC
    # AC is calculated from attributes.base_ac + armor.base_ac + dex + traits
    # Set base_ac very low and remove armor to get minimal AC
    orc.attributes.base_ac = 0
    orc.equipment.armor = None
    target_ac = orc.armor_class

    # Set up a scenario where attack already hits
    ctx = CombatContext(enemies=[orc])

    from agent.mechanics.dice_roller import DiceRoll  # noqa: PLC0415

    ctx.attack_roll = DiceRoll(expression="1d20+5", total=15, raw=10, advantage=None, rolls=[10])

    # Verify attack already hits
    assert target_ac <= 15, f"Roll 15 should hit AC {target_ac}"

    # Should not use Guided Strike
    from agent.effects.trait_effects.support import guided_strike  # noqa: PLC0415

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
    assert war_priest.name == "War Priest"

    # Check it's a bonus action
    assert war_priest.category == ActionCategory.BONUS
    assert war_priest.type == ActionType.ATTACK

    # Check uses_per_rest is based on WIS modifier (actor has WIS 10, so modifier is 0, but min is 1)
    assert war_priest.uses_per_rest >= 1

    # Should not be available without using Attack action first
    assert not war_priest.is_available(actor.action_economy)

    # Use Attack action
    actor.action_economy.use_standard(ActionType.ATTACK)

    # Now should be available
    assert war_priest.is_available(actor.action_economy)

    # Execute the attack
    ctx = CombatContext()
    war_priest.execute(actor, orc, ctx)

    # Should consume one use
    war_priest.finalize(actor)
    assert war_priest.current_uses == 1

    # If we've used all available uses, should not be available even with Attack action
    if war_priest.uses_per_rest == 1:
        actor.action_economy.restore_turn()
        actor.action_economy.use_standard(ActionType.ATTACK)
        assert not war_priest.is_available(actor.action_economy)

    # After rest, uses should be restored
    war_priest.rest()
    assert war_priest.current_uses == 0


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
    from agent.services.level_service import LevelService  # noqa: PLC0415

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
    assert isinstance(magic_weapon, BonusSupportSpellAction)

    # Check it requires concentration
    assert magic_weapon.requires_concentration

    # Check targeting and range
    assert magic_weapon.targeting == TargetingType.SINGLE
    assert magic_weapon.range == 2  # Touch range

    # Check the condition
    assert len(magic_weapon.apply_conditions) == 1
    condition = magic_weapon.apply_conditions[0]
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
