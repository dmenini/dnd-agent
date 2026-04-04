from agent.actions.base import ActionCategory
from agent.actions.common.spell import BonusSupportSpellAction
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
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
