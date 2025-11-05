from pydantic import BaseModel, Field

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.narrative import NarrativeAttributes
from agent.character.stats import Stats
from agent.jobs.base import JobType
from agent.jobs.fighter import Fighter
from agent.jobs.mage import Mage


class CharacterBuilder(BaseModel):
    name: str = Field(description="Character name")
    icon: str = Field(description="Icon on the map")
    party: str = Field(description="Party name (shared with the other players)")
    job: JobType = Field(description="Character class/job")
    stats: Stats = Field(
        description=(
            "Attributes derived from the character background. Free assignment, but total points must be below 72."
        )
    )
    race: str = Field(description="Race")
    backstory: str = Field(description="Backstory")
    personality: list[str] = Field(description="Personality traits.")
    alignment: str = Field(description="Categorization of the ethical and moral perspective.")
    summary: str = Field(description="Short summary of the character profile.")

    def to_character(self) -> Character:
        if self.job == JobType.FIGHTER:
            job = Fighter
        elif self.job == JobType.MAGE:
            job = Mage
        else:
            job = None

        return Character(
            id=self.name.lower().replace(" ", "-"),
            name=self.name,
            icon=self.icon,
            is_player=True,
            level=1,
            experience=0,
            attributes=Attributes.model_validate(self.stats.model_dump()),
            job=job,
            party=Party(id=self.party.lower().replace(" ", "-"), name=self.party, is_player_party=True),
            narrative=NarrativeAttributes(
                race=self.race,
                backstory=self.backstory,
                personality=self.personality,
                alignment=self.alignment,
                summary=self.summary,
            ),
        )
