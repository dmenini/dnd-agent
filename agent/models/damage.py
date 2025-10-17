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

    def __str__(self) -> str:
        op_symbol = "+" if self.operation == "add" else "x"
        return f"{self.type.value} {op_symbol}{self.value}"


class DamageResistance(DamageComponent):
    value: float = Field(ge=0, le=1)
    operation: Literal["add"] = "add"

    def __str__(self) -> str:
        return f"{self.type.value} RES: {self.value:.0%}"


class DamageVulnerability(DamageComponent):
    value: float = Field(ge=0, le=1)
    operation: Literal["add"] = "add"

    def __str__(self) -> str:
        return f"{self.type.value} VUL: {self.value:.0%}"


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

    def __str__(self) -> str:
        parts = []

        # Raw components
        comp_str = ", ".join(str(c) for c in self.components)
        if comp_str:
            parts.append(comp_str)

        # Resistances
        if self.resistances:
            res_str = ", ".join(str(r) for r in self.resistances)
            parts.append(res_str)

        # Vulnerabilities
        if self.vulnerabilities:
            vul_str = ", ".join(str(v) for v in self.vulnerabilities)
            parts.append(vul_str)

        return " | ".join(parts)
