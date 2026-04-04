from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SkipValidation, computed_field, field_serializer, field_validator

from agent.actions.base import Action
from agent.actions.common.evocation import EvocationSpellAction
from agent.actions.common.spell import AttackSpellAction, HealingSpellAction, SupportSpellAction
from agent.actions.registry import ActionRegistry
from agent.character.abilities import AbilityType
from agent.character.attributes import Attributes
from agent.character.equipment import Equipment
from agent.character.narrative import NarrativeAttributes
from agent.character.resources import ActionEconomy, SpellSlots
from agent.effects.base import ModifierTrait, Trait, normalize_id
from agent.effects.evocations.base import Evocation
from agent.effects.status_effects.base import StatusEffect
from agent.logs.log_event import LogEvent, LogLevel
from agent.logs.log_registry import get_log_registry
from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.damage import Damage
from agent.models.enums import EventType, FeatureId
from agent.models.position import Position

registry = get_log_registry()


class CharacterBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    icon: str
    is_player: bool = False
    level: int = 1
    experience: int = 0
    pos: Position = Position(x=0, y=0)
    attributes: Attributes = Field(default_factory=Attributes)
    narrative: NarrativeAttributes = Field(default_factory=NarrativeAttributes)
    stealth_value: int = 0

    spells: list[AttackSpellAction | SupportSpellAction | HealingSpellAction | EvocationSpellAction] = Field(
        default_factory=list
    )
    special_abilities: list[Action] = Field(default_factory=list)
    passives: list[Trait | ModifierTrait] = Field(default_factory=list)
    evocations: list[Evocation] = Field(default_factory=list)
    status_effects: list[StatusEffect] = Field(default_factory=list)

    spell_slots: SpellSlots = Field(default_factory=SpellSlots)
    action_economy: ActionEconomy = Field(default_factory=ActionEconomy)

    equipment: Equipment = Field(default_factory=Equipment)

    # Test-only: override dice roller for deterministic rolls
    cheater_dice: SkipValidation[DiceRoller | None] = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_hp(self) -> int:
        return self.attributes.max_hp(level=self.level)

    def proficiency_bonus(self, reference: Enum) -> int:
        if not self.attributes.has_proficiency(reference):
            return 0

        bonus = self.attributes.proficiency_bonus(level=self.level)
        if self.attributes.has_expertise(reference):
            bonus *= 2

        return bonus

    @computed_field  # type: ignore[prop-decorator]
    @property
    def spell_save_dc(self) -> int:
        return self.attributes.spell_save_dc(level=self.level)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def speed(self) -> float:
        return self.attributes.speed()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_alive(self) -> bool:
        return self.attributes.hp > 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_hidden(self) -> bool:
        return self.stealth_value > 0

    def save_roll(self, ability: AbilityType, *, is_spell: bool = False) -> DiceRoll:
        raise NotImplementedError

    def los_distance(self, target: Position) -> float:
        """Line of Sight distance from the target."""
        return self.pos.manhattan_distance(target)

    def apply_damage(self, damage: int) -> None:
        self.attributes.hp = max(0, self.attributes.hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.hp = min(self.attributes.hp + amount, self.max_hp)

    def modify_incoming_damage(self, damage: Damage) -> Damage:
        """Apply resistances and vulnerabilities to damage."""
        for dtype in {c.type for c in damage.components}:
            if res := self.attributes.damage_resistance(dtype):
                damage.resistances.append(res)
            if vul := self.attributes.damage_vulnerability(dtype):
                damage.vulnerabilities.append(vul)
        return damage

    def register_passive(self, trait: Trait) -> None:
        """Register a passive trait (idempotent)."""
        # Add to passives list if not already there
        if all(trait.id != p.id for p in self.passives):
            self.passives.append(trait)
            self.log_event(f"{self.name} gained passive trait {trait.name}", log_type=LogLevel.DETAIL)

        # Apply immediately if it's a modifier (even if passive exists, as serialization loses modifiers)
        if trait.event_type == EventType.MODIFIER:
            trait.apply(self)

    def unregister_passive(self, feature_id: FeatureId, source_id: str) -> None:
        source_id = normalize_id(source_id)
        matching_traits = [t for t in self.passives if t.feature_id == feature_id and t.source_id == source_id]

        for trait in matching_traits:
            # Remove modifier if applicable
            if trait.event_type == EventType.MODIFIER:
                self.attributes.remove_modifier(trait.id)

            # Remove from passives
            self.passives.remove(trait)

            self.log_event(f"{self.name} lost passive trait {trait.name}", log_type=LogLevel.DETAIL)

    def trigger_event(self, event: EventType, *args: Any, **kwargs: Any) -> None:
        """Trigger all listeners for the given event type in priority order."""
        listeners = [trait for trait in self.passives if trait.event_type == event]
        listeners.sort(key=lambda t: t.priority)

        for trait in list(listeners):
            trait.apply(*args, **kwargs)

    def notify_state_change(self, field_name: str) -> None:
        """Called whenever an internal property changes."""
        # Find all traits that depend on this field
        dependent_traits = [
            trait
            for trait in self.passives
            if trait.event_type == EventType.MODIFIER and trait.condition_depends_on(field_name)
        ]

        # Re-apply them (they'll check their conditions)
        for trait in dependent_traits:
            trait.apply(self)

    def log_event(
        self, message: str, *, log_type: LogLevel = LogLevel.DETAIL, icon: str = "", show_ai: bool = False
    ) -> None:
        char_icon_pad = f"{self.icon} "
        icon = self.icon if log_type == LogLevel.MAIN else icon
        show_ai = True if log_type == LogLevel.MAIN else show_ai
        event = LogEvent(
            actor_id=self.id,
            icon=icon or char_icon_pad,
            is_player=self.is_player,
            message=message,
            type=log_type,
            show_ai=show_ai,
        )
        registry.append(event)

    @field_serializer("spells", "special_abilities")
    def serialize_actions(self, actions: list[Action]) -> list[dict]:
        return [a.model_dump(mode="json") for a in actions]

    @field_validator("spells", "special_abilities", mode="before")
    @classmethod
    def deserialize_action(cls, v: Any) -> list[Action]:
        if not isinstance(v, list):
            msg = f"Invalid action payload: {v}"
            raise TypeError(msg)

        actions = []
        for el in v:
            # If it's already an Action instance, return as-is
            if isinstance(el, Action):
                actions.append(el)

            # Otherwise, assume it's a dict with an "id"
            elif isinstance(el, dict):
                el_copy = el.copy()
                id_ = el_copy.pop("id")
                feature_id = FeatureId(id_)
                actions.append(ActionRegistry.create(id_=feature_id, **el_copy))

            else:
                msg = f"Invalid action payload: {v}"
                raise TypeError(msg)

        return actions
