from agent.actions.base import ActionCategory
from agent.actions.common.spell import BonusSupportSpellAction
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.jobs.cleric import Cleric, WarDomain
from agent.models.damage import DamageType
from agent.models.enums import FeatureId
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
