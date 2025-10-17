import pytest

from agent.models.damage import Damage, DamageComponent, DamageResistance, DamageType, DamageVulnerability


@pytest.mark.parametrize(
    ("components", "resistances", "vulnerabilities", "expected_total"),
    [
        # Case 1: single slashing damage, no resistances
        ([DamageComponent(value=10, type=DamageType.SLASHING)], [], [], 10),
        # Case 2: slashing + fire, fire has 50% resistance
        (
            [DamageComponent(value=10, type=DamageType.SLASHING), DamageComponent(value=2, type=DamageType.FIRE)],
            [DamageResistance(value=0.5, type=DamageType.FIRE)],
            [],
            11,  # 10 + (2 * 0.5) = 11
        ),
        # Case 3: additive + multiplicative, no resistances
        (
            [
                DamageComponent(value=10, type=DamageType.SLASHING),
                DamageComponent(value=2, type=DamageType.COLD, operation="mul"),
            ],
            [],
            [],
            10,  # 10 + (0 * 2) = 10
        ),
        # Case 4: additive + multiplicative + resistance
        (
            [
                DamageComponent(value=10, type=DamageType.SLASHING),
                DamageComponent(value=2, type=DamageType.FIRE),
                DamageComponent(value=2, type=DamageType.COLD, operation="mul"),
            ],
            [DamageResistance(value=1.0, type=DamageType.FIRE)],  # FIRE fully resisted
            [],
            10,  # 10 + (2 * 0) + (0 * 2)
        ),
        # Case 5: additive + multiplicative + vulnerability
        (
            [
                DamageComponent(value=10, type=DamageType.SLASHING),
                DamageComponent(value=3, type=DamageType.FIRE, operation="add"),
                DamageComponent(value=3, type=DamageType.FIRE, operation="mul"),
            ],
            [],
            [DamageVulnerability(value=1.0, type=DamageType.FIRE)],  # FIRE doubled
            46,  # 10 + ((3 * 2) * (3 * 2))
        ),
    ],
)
def test_damage_total(
    components: list[DamageComponent],
    resistances: list[DamageResistance],
    vulnerabilities: list[DamageVulnerability],
    expected_total: int,
) -> None:
    damage = Damage(components=components, resistances=resistances, vulnerabilities=vulnerabilities)
    assert damage.total == expected_total
