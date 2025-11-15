from agent.actions.base import ActionCategory, ActionType
from agent.character.character import Character
from agent.character.collection import ActionExtension
from agent.effects.trait_effects.turn import (
    cannot_act_effect,
    cannot_move_effect,
    extra_actions_effect,
    half_attacks_effect,
)


def test_cannot_move_effect_disables_movement(actor: Character) -> None:
    actor.action_economy.movement_available = True
    cannot_move_effect(actor)
    assert actor.action_economy.movement_available is False


def test_cannot_act_effect_disables_actions(actor: Character) -> None:
    actor.action_economy.can_act = True
    cannot_act_effect(actor)
    assert actor.action_economy.can_act is False


def test_extra_actions_effect_adds_actions(actor: Character) -> None:
    actor.action_economy.action_extensions = []
    extensions = [
        ActionExtension(category=ActionCategory.STANDARD, allowed_actions=[ActionType.ATTACK], source="a"),
        ActionExtension(category=ActionCategory.BONUS, allowed_actions=[ActionType.DASH], source="a"),
    ]

    extra_actions_effect(actor, extensions)

    assert len(actor.action_economy.action_extensions) == len(extensions)
    assert all(ext in actor.action_economy.action_extensions for ext in extensions)


def test_half_attacks_effect_removes_half_attack_extensions(actor: Character) -> None:
    # Create 3 attack extensions
    attack_exts = [
        ActionExtension(category=ActionCategory.STANDARD, allowed_actions=[ActionType.ATTACK], source="a")
        for _ in range(3)
    ]
    # Create 1 non-attack extension to ensure it's ignored
    dash_ext = ActionExtension(category=ActionCategory.BONUS, allowed_actions=[ActionType.DASH], source="a")

    actor.action_economy.action_extensions = [*attack_exts, dash_ext]

    half_attacks_effect(actor)

    # Half (rounded up) of 3 attack extensions should remain: ceil(3 / 2) = 2
    remaining_attacks = [
        ext
        for ext in actor.action_economy.action_extensions
        if ActionType.ATTACK in ext.allowed_actions  # type: ignore[operator]
    ]
    assert len(remaining_attacks) == 2
    # The dash extension should remain untouched
    assert dash_ext in actor.action_economy.action_extensions
