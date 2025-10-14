from typing import Self

from pydantic import BaseModel, computed_field, Field

from agent.actions.attack import MainHandAttackAction, OffHandAttackAction, RangedAttackAction, SpellAction
from agent.actions.base import Action, ActionEconomy
from agent.actions.dash import DashAction
from agent.actions.dodge import DodgeAction
from agent.actions.move import MovementAction
from agent.effects.base import StatusEffect
from agent.models.enums import ConditionType, SpellLevel, StatType, WeaponType
from agent.models.position import Position
from agent.models.weapons import FinesseWeapon, MeleeWeapon, RangedWeapon, Spell

DEFAULT_STAT = 10
ADVANTAGE_THRESHOLD = 16
DISADVANTAGE_THRESHOLD = 8


class Party(BaseModel):
    id: str
    name: str
    is_player_party: bool = False


class Stats(BaseModel):
    strength: int = DEFAULT_STAT
    dexterity: int = DEFAULT_STAT
    constitution: int = DEFAULT_STAT
    intelligence: int = DEFAULT_STAT
    wisdom: int = DEFAULT_STAT
    charisma: int = DEFAULT_STAT

    def modifier(self, stat: StatType) -> int:
        val = self.__getattribute__(stat.value)
        return (val - DEFAULT_STAT) // 2

    def advantage(self, stat: StatType) -> bool | None:
        val = self.__getattribute__(stat.value)
        if val and val >= ADVANTAGE_THRESHOLD:
            return True
        if val and val <= DISADVANTAGE_THRESHOLD:
            return False
        return None


class SpellSlots(BaseModel):
    slots: dict[SpellLevel, int] = Field(
        default_factory=lambda: {
            SpellLevel.LEVEL_1: 2,
            SpellLevel.LEVEL_2: 0,
            SpellLevel.LEVEL_3: 0,
        }
    )  # default low-level caster
    max_slots: dict[SpellLevel, int] = Field(
        default_factory=lambda: {
            SpellLevel.LEVEL_1: 2,
            SpellLevel.LEVEL_2: 0,
            SpellLevel.LEVEL_3: 0,
        }
    )

    def has_slot(self, level: SpellLevel) -> bool:
        """Check if there are slots left for the given spell level. Cantrips are always available."""
        if level == SpellLevel.CANTRIP:
            return True
        return self.slots.get(level, 0) > 0

    def consume(self, level: SpellLevel) -> None:
        if not self.has_slot(level):
            msg = f"No spell slots remaining for level {level}"
            raise ValueError(msg)

        if level != SpellLevel.CANTRIP:
            self.slots[level] -= 1

    def restore_all(self) -> None:
        """Restore all resources. Must be done after combat ends."""
        self.slots = self.max_slots.copy()


class Attributes(BaseModel):
    base_hp: int = 8
    base_ac: int = 2
    base_speed: float = 6.0
    vision_range: float = 10.0
    base_crit_multiplier: int = 2
    mana: int = 0
    max_mana: int = 0

    # dynamic fields updated during play
    current_hp: int = 8
    current_movement: float = 6.0

    def compute_max_hp(self, level: int, stats: Stats) -> int:
        """HP grows with level and Constitution modifier."""
        return self.base_hp + (level - 1) * (5 + stats.modifier(StatType.CON))

    def compute_ac(self, stats: Stats, dex_cap: int | None = None) -> int:
        """Base AC + DEX modifier (possibly capped by armor)."""
        dex_mod = stats.modifier(StatType.DEX)
        if dex_cap is not None:
            dex_mod = min(dex_mod, dex_cap)
        return self.base_ac + dex_mod

    def compute_initiative(self, stats: Stats) -> int:
        """Derived initiative bonus."""
        return stats.modifier(StatType.DEX)

    def compute_speed(self, stats: Stats) -> float:  # noqa: ARG002
        """Base speed, possibly affected by conditions later."""
        return self.base_speed


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
    stats: Stats = Stats()
    status_effects: list[StatusEffect] = []
    proficiencies: list[WeaponType] = []

    main_hand: MeleeWeapon | FinesseWeapon | None = None
    off_hand: MeleeWeapon | FinesseWeapon | None = None
    ranged: RangedWeapon | None = None
    spells: list[Spell] = []
    special_abilities: list[Action] = []

    spell_slots: SpellSlots = SpellSlots()
    action_economy: ActionEconomy = ActionEconomy()
    turn_done: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ac(self) -> int:
        """Armor Class is derived from DEX and equipment."""
        return self.attributes.compute_ac(stats=self.stats)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_hp(self) -> int:
        return self.attributes.compute_max_hp(stats=self.stats, level=self.level)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def initiative_modifier(self) -> int:
        return self.attributes.compute_initiative(stats=self.stats)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def speed(self) -> float:
        return self.attributes.compute_speed(stats=self.stats)

    def move(self, destination: Position, *, dash: bool = False) -> None:
        self.pos = destination
        distance_cost = self.distance(destination)
        if dash:
            distance_cost /= 2  # Dash halves cost
        self.attributes.current_movement = max(self.attributes.current_movement - distance_cost, 0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def proficiency_bonus(self) -> int:
        return 2 + (self.level - 1) // 4

    @property
    def is_alive(self) -> bool:
        return self.attributes.current_hp > 0

    def receive_damage(self, damage: int) -> None:
        for effect in self.status_effects:
            damage = effect.on_receive_damage(self, damage)
        self.apply_damage(damage)

    def apply_damage(self, damage: int) -> None:
        self.attributes.current_hp = max(0, self.attributes.current_hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.current_hp = min(self.attributes.current_hp + amount, self.max_hp)

    def has_effect(self, cond: ConditionType) -> bool:
        existing_conditions = {c.type for c in self.status_effects}
        return cond in existing_conditions

    def start_turn(self):
        self.turn_done = False

        self.attributes.current_movement = self.speed
        self.action_economy.restore_all()

        for effect in self.status_effects:
            effect.on_turn_start(self)

        # Remove expired effects
        self.status_effects = [eff for eff in self.status_effects if not eff.is_expired()]

    def end_turn(self) -> None:
        for effect in self.status_effects:
            effect.on_turn_end(self)

        # Remove expired effects
        self.status_effects = [eff for eff in self.status_effects if not eff.is_expired()]

        self.turn_done = True

    def end_round(self) -> None:
        pass

    def apply_status(self, effect: StatusEffect) -> None:
        if not self.has_effect(effect.type):
            self.status_effects.append(effect)
        else:
            existing_effect = next(eff for eff in self.status_effects if eff.type == effect.type)
            existing_effect.duration = effect.duration

        effect.on_apply(self)

    def modify_incoming_damage(self, damage: int) -> int:
        for effect in self.status_effects:
            damage = effect.on_receive_damage(self, damage)
        return damage

    def modify_outgoing_damage(self, target: Self, damage: int) -> int:
        for effect in self.status_effects:
            damage = effect.on_attack(self, target, damage)
        return damage

    def has_resources(self) -> bool:
        has_bonus = self.off_hand is not None and (self.action_economy.bonus_actions > 0)
        main_hand = self.main_hand or self.ranged or self.spells
        has_main = main_hand is not None and (self.action_economy.standard_actions > 0)
        has_movement = self.action_economy.movement_available
        return has_main or has_bonus or has_movement

    def available_actions(self) -> dict[str, Action]:
        all_actions: list[Action] = [
            MovementAction(range=self.speed),
            DashAction(range=self.speed),
            DodgeAction(),
        ]

        # Equipment-based actions
        equipment_map = [
            (self.main_hand, MainHandAttackAction),
            (self.off_hand, OffHandAttackAction),
            (self.ranged, RangedAttackAction),
        ]

        for eq, action_cls in equipment_map:
            if eq:
                action = action_cls.from_weapon(weapon=eq)  # type: ignore[attr-defined]
                all_actions.append(action)

        # Spells (only if action available and slot available)
        for spell in self.spells:
            if self.spell_slots.has_slot(spell.level):
                action = SpellAction.from_spell(spell)
                all_actions.append(action)

        # Special abilities (can have their own categories)
        all_actions += self.special_abilities

        return {action.id: action for action in all_actions if action.is_available(self.action_economy)}

    def distance(self, target: Position) -> float:
        return self.pos.manhattan_distance(target)
