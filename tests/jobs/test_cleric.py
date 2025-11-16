from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.cleric import Cleric
from agent.models.enums import FeatureId


def test_cleric(actor: Character) -> None:
    # Setup actor as a Cleric and apply features
    actor.armor = Armor(name="Glass", armor_type=ArmorType.LIGHT, base_ac=2)
    actor.change_job(Cleric)

    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.DIVINE_RESTORATION in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.BLESS in spells
    assert FeatureId.SACRED_FLAME in spells

    assert any(t.feature_id == FeatureId.AC_BONUS_WITH_ARMOR_TYPES for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 1


def test_cleric_serialization(actor: Character) -> None:
    actor.change_job(Cleric)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    assert actor2.special_abilities == actor.special_abilities
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
