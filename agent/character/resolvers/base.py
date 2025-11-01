from collections import defaultdict
from typing import Any

from pydantic import BaseModel, PrivateAttr, computed_field, field_validator

from agent.actions.base import Action
from agent.actions.common.spell import AttackSpellAction, SupportSpellAction
from agent.actions.registry import ActionRegistry
from agent.character.attributes import Attributes
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.effects.base import Trait, TraitEffect, normalize_id
from agent.effects.registry import TraitRegistry
from agent.equipment.armor import Armor
from agent.logs.log_event import Icon, LogEvent, LogLevel
from agent.logs.log_registry import get_log_registry
from agent.mechanics.dice_roller import DiceRoll
from agent.models.constants import EventType
from agent.models.damage import Damage
from agent.models.enums import FeatureId
from agent.models.position import Position

registry = get_log_registry()


class CharacterBase(BaseModel):
    id: str
    name: str
    icon: str
    is_player: bool = False
    level: int = 1
    experience: int = 0
    pos: Position = Position(x=0, y=0)
    attributes: Attributes = Attributes()
    stealth_value: int = 0

    spells: list[AttackSpellAction | SupportSpellAction] = []
    abilities: list[Action] = []
    passives: list[Trait] = []

    # Defined for typing to work
    action_economy: ActionEconomy
    armor: Armor | None = None

    _event_listeners: dict[str, list[TraitEffect]] = PrivateAttr(default_factory=lambda: defaultdict(list))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_hp(self) -> int:
        return self.attributes.max_hp(level=self.level)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def proficiency_bonus(self) -> int:
        return self.attributes.proficiency_bonus(level=self.level)

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

    def save_roll(self, save_stat: StatType, *, is_spell: bool = False) -> DiceRoll:
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
        self.passives.append(trait)
        effect = trait.get_effect()
        self.register_listener(effect)

        if effect.event_type == EventType.MODIFIER:
            effect.callback(self)

    def unregister_passive(self, feature_id: FeatureId, source_id: str) -> None:
        source_id = normalize_id(source_id)
        matching_traits = [t for t in self.passives if t.feature_id == feature_id and t.source_id == source_id]
        for trait in matching_traits:
            self.unregister_modifier(trait.id)
            self.unregister_listeners(trait.id)
            self.passives.remove(trait)

    def unregister_modifier(self, source_id: str) -> None:
        source_id = normalize_id(source_id)
        modifier = self.attributes.remove_modifier(source_id)
        if modifier:
            self.log_event(
                f"Removed modifier {modifier.attribute}={modifier.value} from {self.name}",
                icon=Icon.EFFECT_EXPIRED,
                log_type=LogLevel.DEBUG,
            )

    def register_listener(self, event: TraitEffect) -> None:
        """Register a listener for a given event."""
        self._event_listeners[event.event_type.value].append(event)
        self.log_event(
            f"Added listener {event.source_id} for {event.event_type.value}",
            icon=Icon.EFFECT_APPLIED,
            log_type=LogLevel.DEBUG,
        )

    def unregister_listeners(self, source_id: str) -> None:
        """Remove all listeners registered by a given source (e.g., a trait)."""
        for event, listeners in self._event_listeners.items():
            before = len(listeners)
            self._event_listeners[event] = [event for event in listeners if event.source_id != source_id]
            after = len(self._event_listeners[event])
            if before != after:
                self.log_event(
                    f"Removed {before - after} listeners from event '{event}'",
                    icon=Icon.EFFECT_EXPIRED,
                    log_type=LogLevel.DEBUG,
                )

    def trigger_event(self, event: EventType, *args: Any, **kwargs: Any) -> None:
        """Trigger all listeners for the given event type in priority order."""
        events = self._event_listeners.get(event.value, [])
        events.sort(key=lambda e: e.priority)
        for e in list(events):
            e.callback(*args, **kwargs)

    def notify_state_change(self, field_name: str) -> None:
        """Called whenever an internal property changes."""
        for trait in self.passives:
            effect = trait.get_effect()
            if effect.condition_depends_on(field_name):
                self.trigger_event(EventType.MODIFIER, target=self)

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

    @field_validator("spells", "abilities", mode="before")
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
                id_ = el.pop("id")
                feature_id = FeatureId(id_)
                actions.append(ActionRegistry.create(id_=feature_id, **el))

            else:
                msg = f"Invalid action payload: {v}"
                raise TypeError(msg)

        return actions

    @field_validator("passives", mode="before")
    @classmethod
    def deserialize_traits(cls, v: Any) -> list[Trait]:
        if not isinstance(v, list):
            msg = f"Invalid trait payload: {v}"
            raise TypeError(msg)

        passives = []
        for el in v:
            # If it's already a Trait instance, return as-is
            if isinstance(el, Trait):
                passives.append(el)

            # Otherwise, assume it's a dict with an "id"
            elif isinstance(el, dict):
                id_ = el.pop("feature_id")
                feature_id = FeatureId(id_)
                passives.append(TraitRegistry.create(feature_id=feature_id, **el))

            else:
                msg = f"Invalid trait payload: {v}"
                raise TypeError(msg)

        return passives
