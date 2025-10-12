from pydantic import BaseModel, computed_field

from agent.models.action import Action, ActionCategory, ActionOption
from agent.models.enums import Condition, StatType
from agent.models.weapons import MeleeWeapon, RangeWeapon, Spell

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
    pos: tuple[int, int]
    party: Party
    is_player: bool = False
    level: int = 1
    experience: int = 0
    attributes: Attributes = Attributes()
    stats: Stats = Stats()
    conditions: list[Condition] = []

    main_hand: MeleeWeapon | None = None
    off_hand: MeleeWeapon | None = None
    ranged: RangeWeapon | None = None
    spells: list[Spell] = []
    special_abilities: list[Action] = []

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

    @property
    def is_alive(self) -> bool:
        return self.attributes.current_hp > 0

    def apply_damage(self, damage: int) -> None:
        self.attributes.current_hp = max(0, self.attributes.current_hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.current_hp = min(self.attributes.current_hp + amount, self.max_hp)

    def apply_condition(self, cond: Condition) -> None:
        if cond not in self.conditions:
            self.conditions.append(cond)

    def remove_condition(self, cond: Condition) -> None:
        if cond in self.conditions:
            self.conditions.remove(cond)

    def attack_modifier(self, action: Action) -> int:
        return self.stats.modifier(action.stat) + action.magical_bonus

    def crit_multiplier(self, action: Action) -> int:  # noqa: ARG002
        return self.attributes.base_crit_multiplier

    def available_actions(self) -> dict[str, ActionOption]:
        actions: dict[str, ActionOption] = {}

        # List all equipment with the category to apply
        equipment_map = [
            (self.main_hand, ActionCategory.STANDARD),
            (self.off_hand, ActionCategory.BONUS),
            (self.ranged, ActionCategory.STANDARD),
        ]

        for eq, category in equipment_map:
            if eq:
                action = eq.to_action(category)
                actions[action.id] = action

        # Spells always standard action
        for spell in self.spells:
            action = spell.to_action(ActionCategory.STANDARD)
            actions[action.id] = action

        # Special abilities
        for ability in self.special_abilities:
            actions[ability.id] = ability

        return actions
