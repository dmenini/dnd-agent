from enum import Enum

from pydantic import BaseModel

from agent.models.enums import Advantage

DEFAULT_ABILITY_SCORE = 10
ADVANTAGE_THRESHOLD = 16
DISADVANTAGE_THRESHOLD = 8


class AbilityType(str, Enum):
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


class Abilities(BaseModel):
    strength: int = DEFAULT_ABILITY_SCORE
    dexterity: int = DEFAULT_ABILITY_SCORE
    constitution: int = DEFAULT_ABILITY_SCORE
    intelligence: int = DEFAULT_ABILITY_SCORE
    wisdom: int = DEFAULT_ABILITY_SCORE
    charisma: int = DEFAULT_ABILITY_SCORE

    def ability_modifier(self, ability: AbilityType) -> int:
        val = self.__getattribute__(ability.value)
        return (val - DEFAULT_ABILITY_SCORE) // 2

    def ability_advantage(self, ability: AbilityType) -> Advantage:
        val = self.__getattribute__(ability.value)
        if val and val >= ADVANTAGE_THRESHOLD:
            return Advantage.ADVANTAGE
        if val and val <= DISADVANTAGE_THRESHOLD:
            return Advantage.DISADVANTAGE
        return Advantage.NEUTRAL

    def __str__(self) -> str:
        return (
            f"STR {self.strength}, DEX {self.dexterity}, CON {self.constitution}, "
            f"INT {self.intelligence}, WIS {self.wisdom}, CHA {self.charisma}"
        )


class SkillType(str, Enum):
    # Strength
    ATHLETICS = "athletics"

    # Dexterity
    ACROBATICS = "acrobatics"
    SLEIGHT_OF_HAND = "sleight_of_hand"
    STEALTH = "stealth"

    # Intelligence
    ARCANA = "arcana"
    HISTORY = "history"
    INVESTIGATION = "investigation"
    NATURE = "nature"
    RELIGION = "religion"

    # Wisdom
    ANIMAL_HANDLING = "animal_handling"
    INSIGHT = "insight"
    MEDICINE = "medicine"
    PERCEPTION = "perception"
    SURVIVAL = "survival"

    # Charisma
    DECEPTION = "deception"
    INTIMIDATION = "intimidation"
    PERFORMANCE = "performance"
    PERSUASION = "persuasion"

    def to_ability(self) -> AbilityType:
        if self == SkillType.ATHLETICS:
            return AbilityType.STR

        if self in {SkillType.ACROBATICS, SkillType.SLEIGHT_OF_HAND, SkillType.STEALTH}:
            return AbilityType.DEX

        if self in {SkillType.ARCANA, SkillType.HISTORY, SkillType.INVESTIGATION, SkillType.NATURE, SkillType.RELIGION}:
            return AbilityType.INT

        if self in {
            SkillType.ANIMAL_HANDLING,
            SkillType.INSIGHT,
            SkillType.MEDICINE,
            SkillType.PERCEPTION,
            SkillType.SURVIVAL,
        }:
            return AbilityType.WIS

        if self in {SkillType.DECEPTION, SkillType.INTIMIDATION, SkillType.PERFORMANCE, SkillType.PERSUASION}:
            return AbilityType.CHA

        msg = f"No associated stat for skill: {self.value}"
        raise ValueError(msg)
