from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.feature import FeatureId
from agent.jobs.fighter import Fighter


def test_fighter(actor: Character) -> None:
    actor.armor = Armor(name="Armor", armor_type=ArmorType.HEAVY, base_ac=5)
    actor.change_job(Fighter)

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND for a in actor.abilities)

    assert FeatureId.AC_BONUS_WITH_ARMOR in actor.traits
    assert actor.attributes.get_modifiers("ac")[0].value == 1
