import math
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, computed_field


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
    value: float
    type: DamageType
    operation: Literal["add", "mul"] = "add"


class DamageResistance(DamageComponent):
    value: float = Field(ge=0, le=1)


class DamageVulnerability(DamageComponent):
    value: float = Field(ge=0, le=1)


class Damage(BaseModel):
    components: list[DamageComponent]
    resistances: list[DamageResistance] = []
    vulnerabilities: list[DamageVulnerability] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(
        self,
    ) -> int:
        """
        Apply resistances/vulnerabilities by type and return final damage.

        For each damage type:
            total_type = (sum of additive components of that type after resistances)
                         * (sum of multiplicative components of that type after resistances)
        Final total = sum of total_type across all damage types.
        """
        type_totals: dict[DamageType, float] = {}

        # Group additive and multiplicative components by type
        for dtype in {comp.type for comp in self.components}:
            # Additive part
            add_sum = sum(
                comp.value * self._apply_mods(dtype)
                for comp in self.components
                if comp.type == dtype and comp.operation == "add"
            )

            # Multiplicative part
            mul_factor = (
                sum(
                    comp.value * self._apply_mods(dtype)
                    for comp in self.components
                    if comp.type == dtype and comp.operation == "mul"
                )
                or 1
            )

            type_totals[dtype] = add_sum * mul_factor

        return math.ceil(sum(type_totals.values()))

    def _apply_mods(self, dtype: DamageType) -> float:
        factor = 1.0
        factor -= sum(res.value for res in self.resistances if res.type == dtype)
        factor += sum(vul.value for vul in self.vulnerabilities if vul.type == dtype)
        return factor
