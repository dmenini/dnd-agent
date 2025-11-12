from pydantic import BaseModel, Field, field_validator

from agent.character.abilities import Abilities, SkillType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.narrative import NarrativeAttributes
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.equipment.base import EquipmentSlot
from agent.jobs.barbarian import Barbarian
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.cleric import Cleric, ClericOptions
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

options_map = {
    JobType.CLERIC: ClericOptions,
}


class CharacterSelections(BaseModel):
    """Stores player's choices during character creation."""

    skill_proficiencies: list[SkillType] = Field(default=[], description="Selected skill proficiencies")
    equipment: dict[EquipmentSlot, str] = Field(default={}, description="Equipment selections by slot")
    features: dict[str, str] = Field(default={}, description="Class feature selections")


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
    selections: CharacterSelections = Field(
        default=CharacterSelections(), description="Player's choices for skills, equipment, and features"
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
        """Convert builder to full Character, applying selections."""
        attrs = Attributes.model_validate(self.abilities.model_dump())

        # Add skill proficiencies from selections
        attrs.proficiencies = [
            Proficiency(source="builder", type=ProficiencyType.SKILL, target=prof)
            for prof in self.selections.skill_proficiencies
        ]

        base_job = job_map[self.job]
        modified_job = self._apply_feature_selections(base_job)

        character = Character(
            id=self.name.lower().replace(" ", "-"),
            name=self.name,
            icon=self.icon,
            is_player=True,
            level=1,
            experience=0,
            attributes=attrs,
            job=modified_job,
            party=Party(id="players", name=party, is_player_party=True),
            narrative=NarrativeAttributes(
                race=self.race,
                backstory=self.backstory,
                personality=self.personality,
                alignment=self.alignment,
                summary=self.summary,
            ),
        )

        # Apply equipment selections
        self._apply_equipment(character)

        return character

    def _apply_feature_selections(self, base_job: CharacterJob) -> CharacterJob:
        """Modify job based on feature selections ."""
        # Example: If Life Domain selected, add domain-specific features
        domain = self.selections.features.get("Divine Domain")
        if domain and "Life Domain" in domain:
            # Add Life Domain features to the job
            # This could involve modifying the features list
            pass

        return base_job

    def _apply_equipment(self, character: Character) -> None:
        """Apply selected equipment to character."""
        for _slot, _choice in self.selections.equipment.items():
            # Define equipment registry to load a piece from an ID
            pass
