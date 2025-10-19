from typing import Any

from pydantic import BaseModel, computed_field

from agent.actions.base import Action
from agent.character.attributes import Attributes, Modifier
from agent.character.resources import ActionEconomy, SpellSlots
from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.equipment.armor import Accessory, Armor, Shield
from agent.equipment.spells import Spell
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponType
from agent.logs.events import Event, EventType, Icon
from agent.logs.log_registry import get_log_registry
from agent.models.damage import Damage
from agent.models.position import Position

registry = get_log_registry()


class Party(BaseModel):
    id: str
    name: str
    is_player_party: bool = False


class Character(BaseModel):
    id: str
    name: str
    icon: str
    pos: Position
    party: Party
    is_player: bool = False
    level: int = 1
    experience: int = 0
    attributes: Attributes = Attributes()
    status_effects: list[StatusEffect] = []
    proficiencies: list[WeaponType] = []
    proficient_saves: list[StatType] = []

    armor: Armor | None = None
    shield: Shield | None = None
    accessories: list[Accessory] = []
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | None = None
    ranged: RangedWeapon | None = None
    spells: list[Spell] = []
    special_abilities: list[Action] = []

    spell_slots: SpellSlots = SpellSlots()
    action_economy: ActionEconomy = ActionEconomy()
    turn_done: bool = True

    def model_post_init(self, _: Any, /) -> None:
        # Equip to apply traits
        if self.armor:
            self.armor.on_equip(self)
        if self.shield:
            self.shield.on_equip(self)
        if self.accessories:
            for acc in self.accessories:
                acc.on_equip(self)
        if self.main_hand:
            self.main_hand.on_equip(self)
        if self.off_hand:
            self.off_hand.on_equip(self)
        if self.ranged:
            self.ranged.on_equip(self)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def armor_class(self) -> int:
        """Armor Class is derived from DEX and equipment."""
        if self.armor:
            ac = self.attributes.ac_bonus(
                armor_type=self.armor.armor_type,
                max_dex_bonus=self.armor.max_dex_bonus,
            )
            ac += self.armor.base_ac

        else:
            ac = self.attributes.ac_bonus(armor_type=None)

        if self.shield:
            ac += self.shield.ac_bonus

        return ac

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_hp(self) -> int:
        return self.attributes.max_hp(level=self.level)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def initiative_modifier(self) -> int:
        return self.attributes.initiative()

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
    def current_speed(self) -> float:
        return self.attributes.speed() - self.action_economy.movement_used

    @property
    def is_alive(self) -> bool:
        return self.attributes.hp > 0

    def move(self, destination: Position) -> None:
        self.pos = destination
        self.log_event(f"New position: {destination}", icon=Icon.MOVE)

    def apply_damage(self, damage: int) -> None:
        self.attributes.hp = max(0, self.attributes.hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.hp = min(self.attributes.hp + amount, self.max_hp)

    def is_immune_to(self, cond: EffectType) -> bool:  # noqa: ARG002
        # TODO: Implement this
        return False

    def modify_incoming_damage(self, damage: Damage) -> Damage:
        """Apply resistances and vulnerabilities to damage."""
        for dtype in {c.type for c in damage.components}:
            if res := self.attributes.damage_resistance(dtype):
                damage.resistances.append(res)
            if vul := self.attributes.damage_vulnerability(dtype):
                damage.vulnerabilities.append(vul)
        return damage

    def has_resources(self) -> bool:
        has_bonus = self.off_hand is not None and (self.action_economy.can_use_bonus())
        main_hand = self.main_hand or self.ranged or self.spells
        has_main = main_hand is not None and (self.action_economy.can_use_standard())
        has_movement = self.action_economy.can_move(self.current_speed)
        return has_main or has_bonus or has_movement

    def distance(self, target: Position) -> float:
        return self.pos.manhattan_distance(target)

    def add_modifier(self, modifier: Modifier) -> None:
        self.attributes.add_modifier(modifier)
        self.log_event(
            f"Added modifier {modifier.attribute}={modifier.value} to {self.name}",
            icon=Icon.EFFECT_APPLIED,
            event_type=EventType.DEBUG,
        )

    def remove_modifier(self, source_id: str) -> None:
        modifier = self.attributes.remove_modifier(source_id)
        if modifier:
            self.log_event(
                f"Removed modifier {modifier.attribute}={modifier.value} from {self.name}",
                icon=Icon.EFFECT_APPLIED,
                event_type=EventType.DEBUG,
            )

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
