from agent.actions.common.spell import AttackSpellAction
from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resources import SpellLevel
from agent.jobs.wizard import Wizard
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.services.job_service import JobService
from tests.conftest import cheater_dice


def make_attack_spell_action() -> AttackSpellAction:
    return AttackSpellAction(
        id="spell",
        name="Basic Spell",
        description="A test spell.",
        targeting=TargetingType.SINGLE,
        damage_dice="1d8",
        damage_type=DamageType.FIRE,
        level=SpellLevel.LEVEL_1,
        ability=AbilityType.INT,
        range=1.5,
    )


def test_attack_hits(actor: Character, target: Character) -> None:
    JobService.change_job(actor, Wizard)
    actor.attributes.intelligence = 16  # +3 modifier and +2 with proficiency
    actor.attributes.spellcasting_ability = AbilityType.INT
    action = make_attack_spell_action()

    # Actor rolls damage (8), target fails save (rolls 1)
    actor.cheater_dice = cheater_dice(value=8)
    target.cheater_dice = cheater_dice(value=1)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Damage: 8 (dice value)
    assert target.attributes.hp == start_hp - 8 - 3

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_misses(actor: Character, target: Character) -> None:
    JobService.change_job(actor, Wizard)
    actor.attributes.spellcasting_ability = AbilityType.INT
    target.attributes.proficiencies = [
        Proficiency(type=ProficiencyType.SAVE, target=AbilityType.INT)
    ]  # Save modifier +2
    action = make_attack_spell_action()

    # Target passes save (rolls 20, well above DC)
    target.cheater_dice = cheater_dice(value=20)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Target resists - no damage
    assert target.attributes.hp == start_hp

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_save_throw_skipped(actor: Character, target: Character) -> None:
    JobService.change_job(actor, Wizard)
    actor.attributes.spellcasting_ability = AbilityType.INT
    action = make_attack_spell_action()
    action.requires_save = False

    # No save required - actor rolls damage (5)
    actor.cheater_dice = cheater_dice(value=5)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - 5

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False
