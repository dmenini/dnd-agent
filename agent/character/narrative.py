from pydantic import BaseModel


class NarrativeAttributes(BaseModel):
    race: str = ""
    backstory: str = ""
    personality: list[str] = []
    alignment: str = ""
    summary: str = ""
