from pydantic import BaseModel

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.stats import Stats
from agent.jobs.base import JobType
from agent.jobs.fighter import Fighter
from agent.jobs.mage import Mage


class CharacterBuilder(BaseModel):
    name: str
    icon: str
    party: str
    stats: Stats
    race: str
    job: JobType

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
        )
