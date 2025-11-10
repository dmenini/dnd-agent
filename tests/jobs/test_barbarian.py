from agent.character.character import Character
from agent.jobs.barbarian import Barbarian
from agent.models.enums import FeatureId


def test_barbarian(actor: Character) -> None:
    actor.change_job(Barbarian)

    # Verify active action is available
    assert any(a.id == FeatureId.RAGE for a in actor.special_abilities)

    assert any(t.feature_id == FeatureId.AC_BONUS_MOD_WITHOUT_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac_mod.constitution")[0].value == 1


def test_barbarian_serialization(actor: Character) -> None:
    actor.change_job(Barbarian)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    assert actor2.special_abilities == actor.special_abilities
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
