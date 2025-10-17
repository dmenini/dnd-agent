from agent.character.character import Character, Party
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import Resistance, Trait, Vulnerability
from agent.equipment.armor import Accessory
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability
from agent.models.position import Position


class CustomEffect(StatusEffect):
    type: EffectType = EffectType.CUSTOM
    duration: int = 2
    _traits: list[Trait] = [
        Resistance(value=0.25, damage_type=DamageType.FIRE),
        Resistance(value=0.25, damage_type=DamageType.COLD),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1


def test_same_effects() -> None:
    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    hero = Character(
        id="hero-id",
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
    )

    hero.start_turn()

    effect1 = CustomEffect()
    effect2 = CustomEffect()

    hero.apply_status(effect1)

    assert hero.status_effects[0].type == EffectType.CUSTOM
    assert hero.status_effects[0].duration == 2
    assert hero.attributes._modifiers["resistance.fire"][0].value == 0.25
    assert hero.attributes._modifiers["resistance.cold"][0].value == 0.25

    hero.end_turn()

    assert hero.status_effects[0].type == EffectType.CUSTOM
    assert hero.status_effects[0].duration == 1
    assert hero.attributes._modifiers["resistance.fire"][0].value == 0.25
    assert hero.attributes._modifiers["resistance.cold"][0].value == 0.25

    hero.apply_status(effect2)

    assert hero.status_effects[0].type == EffectType.CUSTOM
    assert hero.status_effects[0].duration == 2
    assert len(hero.attributes._modifiers["resistance.fire"]) == 1
    assert len(hero.attributes._modifiers["resistance.cold"]) == 1
    assert hero.attributes._modifiers["resistance.fire"][0].value == 0.25
    assert hero.attributes._modifiers["resistance.cold"][0].value == 0.25


def test_different_traits() -> None:
    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    value = 0.5

    acc1 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])
    acc2 = Accessory(name="ring", slot="ring", traits=[Vulnerability(value=value, damage_type=DamageType.FIRE)])

    hero = Character(
        id="hero-id",
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
        accessories=[acc1, acc2],
    )

    attrs = hero.attributes
    assert attrs._modifiers["resistance.fire"][0].value == value
    assert attrs._modifiers["vulnerability.fire"][0].value == value

    assert attrs.compute_resistance(DamageType.FIRE) == DamageResistance(value=value, type=DamageType.FIRE)
    assert attrs.compute_vulnerability(DamageType.FIRE) == DamageVulnerability(value=value, type=DamageType.FIRE)

    hero.start_turn()
    hero.end_turn()

    # Traits don't expire
    assert attrs._modifiers["resistance.fire"][0].value == value
    assert attrs._modifiers["vulnerability.fire"][0].value == value


def test_same_traits() -> None:
    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    value = 0.5

    acc1 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])
    acc2 = Accessory(name="ring", slot="ring", traits=[Resistance(value=value, damage_type=DamageType.FIRE)])

    hero = Character(
        id="hero-id",
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
        accessories=[acc1, acc2],
    )

    attrs = hero.attributes
    assert len(attrs._modifiers["resistance.fire"]) == 2
    assert attrs._modifiers["resistance.fire"][0].value == value
    assert attrs._modifiers["resistance.fire"][1].value == value

    assert attrs.compute_resistance(DamageType.FIRE) == DamageResistance(value=value * 2, type=DamageType.FIRE)
