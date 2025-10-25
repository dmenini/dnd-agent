from agent.character.character import Character
from agent.jobs.feature import FeatureId
from agent.jobs.mage import Mage


def test_mage(actor: Character) -> None:
    # Setup actor as a Mage and apply features
    actor.armor = None
    actor.change_job(Mage)

    abilities = [a.id for a in actor.abilities]
    assert FeatureId.ARCANE_RECOVERY in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.MAGIC_MISSILE in spells

    assert FeatureId.SPELL_SAVE_ADVANTAGE in actor.traits
    assert FeatureId.AC_BONUS_WITHOUT_ARMOR in actor.traits
    assert actor.attributes.get_modifiers("save_advantage.spell")[0].value is True
    assert actor.attributes.get_modifiers("ac")[0].value == 3
