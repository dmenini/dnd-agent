from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.fighter import Fighter
from agent.models.enums import FeatureId


def test_fighter(actor: Character) -> None:
    actor.armor = Armor(name="Armor", armor_type=ArmorType.HEAVY, base_ac=5)
    actor.change_job(Fighter)

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND for a in actor.abilities)

    assert any(t.feature == FeatureId.AC_BONUS_WITH_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 1
