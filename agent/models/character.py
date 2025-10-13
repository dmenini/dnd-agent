from pydantic import BaseModel, Field, computed_field

from agent.models.action import Action, ActionCategory, ActionOption
from agent.models.enums import ActionType, ConditionType, SpellLevel, StatType, TargetingType, WeaponType
from agent.models.weapons import FinesseWeapon, MeleeWeapon, RangeWeapon, Spell

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


class ActionEconomy(BaseModel):
    standard_actions: int = 1
    max_standard_actions: int = 1
    bonus_actions: int = 1
    max_bonus_actions: int = 1
    reaction_available: bool = True
    movement_available: bool = True

    def has_resources(self) -> bool:
        # TODO: extend when movement and reactions are implemented
        return self.standard_actions > 0 or self.bonus_actions > 0

    def consume(self, category: ActionCategory) -> None:
        """Consume the resources used by the action."""
        if category == ActionCategory.STANDARD:
            if self.standard_actions <= 0:
                raise ValueError("No standard actions left")
            self.standard_actions -= 1
        elif category == ActionCategory.BONUS:
            if self.bonus_actions <= 0:
                raise ValueError("No bonus actions left")
            self.bonus_actions -= 1
        elif category == ActionCategory.REACTION:
            if not self.reaction_available:
                raise ValueError("Reaction already used")
            self.reaction_available = False
        elif category == ActionCategory.MOVEMENT:
            if not self.movement_available:
                raise ValueError("Already moved")
            self.movement_available = False

    def restore_all(self) -> None:
        """Restore all resources. Must be done after each round."""
        self.standard_actions = self.max_standard_actions
        self.bonus_actions = self.max_bonus_actions
        self.movement_available = True
        self.reaction_available = True


class Attributes(BaseModel):
    base_hp: int = 8
    base_ac: int = 10
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


class StatusEffect(BaseModel):
    type: ConditionType
    duration: int


class Character(BaseModel):
    id: str
    name: str
    pos: tuple[int, int]
    party: Party
    is_player: bool = False
    level: int = 1
    experience: int = 0
    attributes: Attributes = Attributes()
    stats: Stats = Stats()
    conditions: list[StatusEffect] = []
    proficiencies: list[WeaponType] = []

    main_hand: MeleeWeapon | FinesseWeapon | None = None
    off_hand: MeleeWeapon | FinesseWeapon | None = None
    ranged: RangeWeapon | None = None
    spells: list[Spell] = []
    special_abilities: list[Action] = []

    spell_slots: SpellSlots = SpellSlots()
    action_economy: ActionEconomy = ActionEconomy()

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

    def move(self, destination: tuple[int, int], *, dash: bool = False) -> None:
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

    def apply_damage(self, damage: int) -> None:
        self.attributes.current_hp = max(0, self.attributes.current_hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.current_hp = min(self.attributes.current_hp + amount, self.max_hp)

    def has_effect(self, cond: ConditionType) -> bool:
        existing_conditions = {c.type for c in self.conditions}
        return cond in existing_conditions

    def apply_condition(self, cond: ConditionType, duration: int) -> None:
        if not self.has_effect(cond):
            effect = StatusEffect(type=cond, duration=duration)
            self.conditions.append(effect)
        else:
            existing_effect = next(c for c in self.conditions if c.type == cond)
            existing_effect.duration = duration

    def elapse_conditions(self) -> None:
        for effect in self.conditions:
            effect.duration -= 1

        self.conditions = [c for c in self.conditions if c.duration >= 0]

    def attack_modifier(self, action: Action) -> int:
        weapon_bonus = action.magical_bonus or 0
        prof_bonus = self.proficiency_bonus if action.weapon_type in self.proficiencies else 0
        mod = self.stats.modifier(action.stat) if action.stat else 0
        return mod + weapon_bonus + prof_bonus

    def crit_multiplier(self, action: Action) -> int:  # noqa: ARG002
        return self.attributes.base_crit_multiplier

    def available_actions(self) -> dict[str, ActionOption]:
        actions: dict[str, ActionOption] = {}

        # Standard + Bonus Actions available?
        std_available = self.action_economy.standard_actions > 0
        bonus_available = self.action_economy.bonus_actions > 0

        # Equipment-based actions
        equipment_map = [
            (self.main_hand, ActionCategory.STANDARD),
            (self.off_hand, ActionCategory.BONUS),
            (self.ranged, ActionCategory.STANDARD),
        ]

        for eq, category in equipment_map:
            if eq and (
                (category == ActionCategory.STANDARD and std_available)
                or (category == ActionCategory.BONUS and bonus_available)
            ):
                action = eq.to_action(category)
                actions[action.id] = action

        # Spells (only if action available and slot available)
        if std_available:
            for spell in self.spells:
                if self.spell_slots.has_slot(spell.level):
                    action = spell.to_action()
                    actions[action.id] = action

        # Special abilities (can have their own categories)
        for ability in self.special_abilities:
            if (ability.category == ActionCategory.BONUS and bonus_available) or (
                ability.category == ActionCategory.STANDARD and not std_available
            ):
                actions[ability.id] = ability

        # Dash (always if movement + standard action)
        if std_available and self.action_economy.movement_available:
            actions["dash"] = ActionOption(
                id="dash",
                name="Dash",
                source="Base",
                action_type=ActionType.DASH,
                category=ActionCategory.STANDARD,
                targeting=TargetingType.SELF,
                range=self.speed,
                stat=StatType.DEX,
            )

        if std_available:
            actions["dodge"] = ActionOption(
                id="dodge",
                name="Dodge",
                source="Base",
                action_type=ActionType.DODGE,
                category=ActionCategory.STANDARD,
                targeting=TargetingType.SELF,
                range=self.speed,
                stat=None,
            )

        return actions

    def distance(self, target: tuple[int, int]) -> float:
        return abs(self.pos[0] - target[0]) + abs(self.pos[1] - target[1])  # Manhattan distance
