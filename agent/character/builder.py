from pydantic import BaseModel, Field, field_validator
from pydantic.json_schema import SkipJsonSchema

from agent.character.abilities import Abilities, SkillType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.narrative import NarrativeAttributes
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.equipment.base import EQUIPMENT_TYPES_PER_SLOT, EquipmentSlot
from agent.equipment.inventory import EquipmentPiece
from agent.jobs.barbarian import Barbarian
from agent.jobs.base import CharacterJob, JobType
from agent.jobs.cleric import Cleric, ClericOptions
from agent.jobs.feature import EquipmentChoice, FeatureChoice
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

    skill_proficiencies: list[SkillType] = Field(default=[], description="Selected skill proficiencies.")
    equipment: dict[EquipmentSlot, EquipmentPiece] = Field(default={}, description="Equipment selections by slot.")
    features: dict[str, str] = Field(default={}, description="Class feature selections.")

    def validate_skills(self, options: list[SkillType], max_count: int) -> None:
        invalid = [s for s in self.skill_proficiencies if s not in options]

        if invalid:
            msg = f"Invalid skill choices: {invalid}. Valid options: {options}"
            raise ValueError(msg)

        if len(self.skill_proficiencies) != max_count:
            msg = f"Must choose exactly {max_count} skills. You chose {len(self.skill_proficiencies)}."
            raise ValueError(msg)

    def validate_equipment_choices(self, options: list[EquipmentChoice]) -> None:
        for slot, choice in self.equipment.items():
            # Find the equipment option
            option = next((option for option in options if option.slot == slot), None)
            if not option:
                msg = f"Invalid equipment slot: {slot}"
                raise ValueError(msg)

            if choice.name not in option.options:
                msg = f"Invalid choice '{choice.name}' for {slot}. Options: {option.options}"
                raise ValueError(msg)

            if choice.type not in EQUIPMENT_TYPES_PER_SLOT[slot]:
                msg = f"Invalid equipment slot for equipment type {choice.type.value}: {slot.value}"
                raise ValueError(msg)

    def validate_feature_choices(self, options: list[FeatureChoice]) -> None:
        for name, choice in self.features.items():
            feat_choice = next((f for f in options if f.feature_name == name), None)
            if not feat_choice:
                msg = f"Invalid feature: {name}"
                raise ValueError(msg)

            # Check if choice matches any option (allow partial matching)
            matching_option = None
            for opt in feat_choice.options:
                if choice.lower() in opt.lower() or opt.lower().startswith(choice.lower()):
                    matching_option = opt
                    break

            if not matching_option:
                msg = f"Invalid choice for {name}. Options: {feat_choice.options}"
                raise ValueError(msg)


class CharacterBuilder(BaseModel):
    name: str = Field(description="Character name")
    icon: str = Field(description="Icon on the map (emoji)")
    job: JobType = Field(description="Character class/job")
    race: str = Field(default="human", description="Race")
    backstory: str = Field(default="", description="Comprehensive backstory")
    personality: str = Field(default="", description="Personality traits.")
    alignment: str = Field(default="", description="Categorization of the ethical and moral perspective.")
    summary: str = Field(default="", description="Summary of the character profile.")
    abilities: Abilities = Field(
        default=Abilities(),
        description=(
            f"Abilities derived from the character background. "
            f"Free assignment, but total scores must be below {MAX_SCORES_TOTAL}."
        ),
    )

    # Hide selections so that LLM doesn't try to assign them at the very beginning
    selections: SkipJsonSchema[CharacterSelections] = Field(
        default=CharacterSelections(), description="Player's choices for skills, equipment, and features"
    )

    @field_validator("abilities", mode="after")
    @classmethod
    def total_value(cls, v: Abilities) -> Abilities:
        tot = v.strength + v.wisdom + v.intelligence + v.charisma + v.dexterity + v.constitution
        if tot > MAX_SCORES_TOTAL:
            msg = (
                f"The total scores must be lower than {MAX_SCORES_TOTAL} to maintain game balance. "
                f"Please, revise the scores."
            )
            raise ValueError(msg)
        return v

    def __str__(self) -> str:
        return f"{self.icon} {self.name} - {self.race.title()} {self.job.value.title()}"

    def to_character(self, party: str) -> Character:
        """Convert builder to full Character, applying selections."""
        attrs = Attributes.model_validate(self.abilities.model_dump())

        # Add skill proficiencies from selections
        attrs.proficiencies = [
            Proficiency(source="builder", type=ProficiencyType.SKILL, target=prof)
            for prof in self.selections.skill_proficiencies or []
        ]

        base_job = job_map[self.job]
        modified_job = self._apply_feature_selections(base_job)

        character = Character(
            id=self.name.lower().replace(" ", "-"),
            name=self.name,
            icon=self.icon.strip(),
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
        features = self.selections.features or {}
        domain = features.get("Divine Domain")
        if domain and "Life Domain" in domain:
            # Add Life Domain features to the job
            # This could involve modifying the features list
            pass

        return base_job

    def _apply_equipment(self, character: Character) -> None:
        """Apply selected equipment to character."""
        equipment = self.selections.equipment or {}
        for slot, choice in equipment.items():
            character.equip(item=choice, slot_name=slot)
