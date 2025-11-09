from pydantic import BaseModel, Field

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.narrative import NarrativeAttributes
from agent.character.stats import Stats
from agent.jobs.barbarian import Barbarian
from agent.jobs.base import JobType
from agent.jobs.cleric import Cleric
from agent.jobs.fighter import Fighter
from agent.jobs.wizard import Wizard

job_map = {
    JobType.FIGHTER: Fighter,
    JobType.WIZARD: Wizard,
    JobType.CLERIC: Cleric,
    JobType.BARBARIAN: Barbarian,
}


class CharacterBuilder(BaseModel):
    name: str = Field(description="Character name")
    icon: str = Field(description="Icon on the map (emojy)")
    job: JobType = Field(description="Character class/job")
    stats: Stats = Field(
        default=Stats(),
        description=(
            "Attributes derived from the character background. Free assignment, but total points must be below 72."
        ),
    )
    race: str = Field(default="human", description="Race")
    backstory: str = Field(default="", description="Backstory")
    personality: str = Field(default="", description="Personality traits.")
    alignment: str = Field(default="", description="Categorization of the ethical and moral perspective.")
    summary: str = Field(default="", description="Short summary of the character profile.")

    def to_character(self, party: str) -> Character:
        return Character(
            id=self.name.lower().replace(" ", "-"),
            name=self.name,
            icon=self.icon,
            is_player=True,
            level=1,
            experience=0,
            attributes=Attributes.model_validate(self.stats.model_dump()),
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
