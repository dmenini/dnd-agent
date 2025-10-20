from collections import defaultdict
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, PrivateAttr, computed_field

from agent.character.attributes import Attributes
from agent.character.modifier import Modifier
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.logs.events import Event, EventType, Icon
from agent.logs.log_registry import get_log_registry
from agent.mechanics.dice_roller import DiceRoll
from agent.models.damage import Damage
from agent.models.position import Position

registry = get_log_registry()


class CharacterBase(BaseModel):
    id: str
    name: str
    icon: str
    is_player: bool = False
    level: int = 1
    experience: int = 0
    pos: Position
    attributes: Attributes = Attributes()

    action_economy: ActionEconomy

    _event_listeners: dict[str, list[tuple[str, Callable]]] = PrivateAttr(default_factory=lambda: defaultdict(list))

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

    @property
    def is_alive(self) -> bool:
        return self.attributes.hp > 0

    def save_roll(self, save_stat: StatType, *, is_spell: bool = False) -> DiceRoll:
        raise NotImplementedError

    def distance(self, target: Position) -> float:
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

    def register_modifier(self, modifier: Modifier) -> None:
        self.attributes.add_modifier(modifier)
        self.log_event(
            f"Added modifier {modifier.attribute}={modifier.value} to {self.name}",
            icon=Icon.EFFECT_APPLIED,
            event_type=EventType.DEBUG,
        )

    def unregister_modifier(self, source_id: str) -> None:
        modifier = self.attributes.remove_modifier(source_id)
        if modifier:
            self.log_event(
                f"Removed modifier {modifier.attribute}={modifier.value} from {self.name}",
                icon=Icon.EFFECT_APPLIED,
                event_type=EventType.DEBUG,
            )

    def register_listener(self, event: str, callback: Callable, source_id: str) -> None:
        """Register a listener for a given event name."""
        self._event_listeners[event].append((source_id, callback))
        self.log_event(f"Registered listener {callback.__name__} for {event}", event_type=EventType.DEBUG)

    def unregister_listeners(self, source_id: str) -> None:
        """Remove all listeners registered by a given source (e.g., a trait)."""
        for event, listeners in self._event_listeners.items():
            before = len(listeners)
            self._event_listeners[event] = [(sid, cb) for sid, cb in listeners if sid != source_id]
            after = len(self._event_listeners[event])
            if before != after:
                self.log_event(f"Removed {before - after} listeners from event '{event}'", event_type=EventType.DEBUG)

    def trigger_event(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Trigger all listeners for the given event name."""
        for _, callback in list(self._event_listeners.get(event, [])):
            callback(*args, **kwargs)

    def log_event(
        self, message: str, *, event_type: EventType = EventType.DETAIL, icon: str = "", show_ai: bool = False
    ) -> None:
        icon = self.icon if event_type == EventType.MAIN else icon
        show_ai = True if event_type == EventType.MAIN else show_ai
        event = Event(
            actor_id=self.id,
            icon=icon or self.icon,
            is_player=self.is_player,
            message=message,
            type=event_type,
            show_ai=show_ai,
        )
        registry.append(event)
