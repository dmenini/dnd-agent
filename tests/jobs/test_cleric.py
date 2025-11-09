from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.cleric import Cleric
from agent.models.enums import FeatureId


def test_cleric(actor: Character) -> None:
    # Setup actor as a Cleric and apply features
    actor.armor = Armor(name="Glass", armor_type=ArmorType.LIGHT, base_ac=2)
    actor.change_job(Cleric)

    abilities = [a.id for a in actor.abilities]
    assert FeatureId.DIVINE_RESTORATION in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.BLESS in spells
    assert FeatureId.SACRED_FLAME in spells

    assert any(t.feature_id == FeatureId.SPELL_SAVE_ADVANTAGE for t in actor.passives)
    assert any(t.feature_id == FeatureId.AC_BONUS_WITH_ARMOR_TYPES for t in actor.passives)
    assert actor.attributes.get_modifiers("save_advantage.spell")[0].value is True
    assert actor.attributes.get_modifiers("ac")[0].value == 1
