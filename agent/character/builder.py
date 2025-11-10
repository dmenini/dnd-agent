from pydantic import BaseModel, Field, field_validator

from agent.character.abilities import Abilities, SkillType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.narrative import NarrativeAttributes
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.jobs.barbarian import Barbarian
from agent.jobs.base import JobType
from agent.jobs.cleric import Cleric
from agent.jobs.fighter import Fighter
from agent.jobs.rogue import Rogue
from agent.jobs.wizard import Wizard
from agent.models.constants import MAX_SCORES_TOTAL

job_map = {
    JobType.FIGHTER: Fighter,
    JobType.WIZARD: Wizard,
    JobType.CLERIC: Cleric,
    JobType.BARBARIAN: Barbarian,
    JobType.ROGUE: Rogue,
}


class CharacterBuilder(BaseModel):
    name: str = Field(description="Character name")
    icon: str = Field(description="Icon on the map (emoji)")
    job: JobType = Field(description="Character class/job")
    abilities: Abilities = Field(
        default=Abilities(),
        description=(
            f"Abilities derived from the character background. "
            f"Free assignment, but total scores must be below {MAX_SCORES_TOTAL}."
        ),
    )
    skill_proficiencies: list[SkillType] = Field(
        default=[],
        description="Skill proficiencies derived from the character background.",
        max_length=2,
    )
    race: str = Field(default="human", description="Race")
    backstory: str = Field(default="", description="Backstory")
    personality: str = Field(default="", description="Personality traits.")
    alignment: str = Field(default="", description="Categorization of the ethical and moral perspective.")
    summary: str = Field(default="", description="Short summary of the character profile.")

    @field_validator("abilities", mode="after")
    @classmethod
    def total_value(cls, v: Abilities) -> Abilities:
        tot = v.strength + v.wisdom + v.intelligence + v.charisma + v.dexterity + v.constitution
        if tot > MAX_SCORES_TOTAL:
            msg = f"The total scores must be lower than {MAX_SCORES_TOTAL} to maintain game balance"
            raise ValueError(msg)
        return v

    def to_character(self, party: str) -> Character:
        attrs = Attributes.model_validate(self.abilities.model_dump())
        attrs.proficiencies = [
            Proficiency(source="builder", type=ProficiencyType.SKILL, target=prof) for prof in self.skill_proficiencies
        ]
        return Character(
            id=self.name.lower().replace(" ", "-"),
            name=self.name,
            icon=self.icon,
            is_player=True,
            level=1,
            experience=0,
            attributes=attrs,
            job=job_map[self.job],
            party=Party(id="players", name=party, is_player_party=True),
            narrative=NarrativeAttributes(
                race=self.race,
                backstory=self.backstory,
                personality=self.personality,
                alignment=self.alignment,
                summary=self.summary,
            ),
        )
