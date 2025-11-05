from pydantic import BaseModel


class NarrativeAttributes(BaseModel):
    race: str = ""
    backstory: str = ""
    personality: str = ""
    alignment: str = ""
    summary: str = ""
