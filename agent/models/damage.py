import math
from enum import Enum

from pydantic import BaseModel, Field


class DamageType(str, Enum):
    SLASHING = "slashing"
    PIERCING = "piercing"
    BLUDGEONING = "bludgeoning"
    FIRE = "fire"
    COLD = "cold"
    POISON = "poison"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    RADIANT = "radiant"


class DamageComponent(BaseModel):
    value: int
    type: DamageType


class DamageResistance(DamageComponent):
    value: float = Field(ge=0, le=1)


class DamageVulnerability(DamageComponent):
    value: float = Field(ge=0, le=1)


class Damage(BaseModel):
    components: list[DamageComponent]
    resistances: list[DamageResistance]
    vulnerabilities: list[DamageVulnerability]

    def total(
        self,
    ) -> int:
        """Apply resistances/vulnerabilities by type and return final damage."""
        total = 0.0
        for comp in self.components:
            factor = 1.0

            # Apply resistance multipliers (each can partially stack)
            for res in self.resistances:
                if res.type == comp.type:
                    factor -= res.value

            # Apply vulnerability multipliers
            for vul in self.vulnerabilities:
                if vul.type == comp.type:
                    factor += vul.value

            total += comp.value * factor

        return math.ceil(total)
