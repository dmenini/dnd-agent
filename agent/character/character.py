from typing import Any, Self

from pydantic import BaseModel, computed_field

from agent.actions.attack import MainHandAttackAction, OffHandAttackAction, RangedAttackAction
from agent.actions.base import Action, ActionEconomy
from agent.actions.dash import DashAction
from agent.actions.dodge import DodgeAction
from agent.actions.move import MovementAction
from agent.actions.spell import AttackSpellAction, SupportSpellAction
from agent.actions.wait import WaitAction
from agent.character.attributes import Attributes, Modifier
from agent.character.resources import SpellSlots
from agent.character.stats import Stats, StatType
from agent.effects.base import EffectType, StatusEffect
from agent.equipment.armor import Accessory, Armor
from agent.equipment.spells import AttackSpell, Spell, SupportSpell
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponType
from agent.logs.events import Event, EventType, Icon
from agent.logs.log_registry import get_log_registry
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller
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
    stats: Stats = Stats()
    status_effects: list[StatusEffect] = []
    proficiencies: list[WeaponType] = []
    proficient_saves: list[StatType] = []

    armor: Armor | None = None
    accessories: list[Accessory] = []
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | None = None
    ranged: RangedWeapon | None = None
    spells: list[Spell] = []
    special_abilities: list[Action] = []

    spell_slots: SpellSlots = SpellSlots()
    action_economy: ActionEconomy = ActionEconomy()
    turn_done: bool = True

    _dice: DiceRoller = DiceRoller()

    def model_post_init(self, _: Any, /) -> None:
        # Equip to apply traits
        if self.armor:
            self.armor.on_equip(self)
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_speed(self) -> float:
        return self.attributes.compute_speed(stats=self.stats) - self.action_economy.movement_used

    def move(self, destination: Position, *, dash: bool = False) -> None:
        self.pos = destination
        distance_cost = self.distance(destination)
        if dash:
            distance_cost /= 2  # Dash halves cost
        self.action_economy.movement_used = distance_cost
        self.log_event(f"New position: {destination}", icon=Icon.MOVE)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def proficiency_bonus(self) -> int:
        return 2 + (self.level - 1) // 4

    @property
    def is_alive(self) -> bool:
        return self.attributes.hp > 0

    def apply_damage(self, damage: int) -> None:
        self.attributes.hp = max(0, self.attributes.hp - damage)

    def heal(self, amount: int) -> None:
        self.attributes.hp = min(self.attributes.hp + amount, self.max_hp)

    def has_effect(self, cond: EffectType) -> bool:
        existing_conditions = {c.type for c in self.status_effects}
        return cond in existing_conditions

    def is_immune_to(self, cond: EffectType) -> bool:  # noqa: ARG002
        # TODO: Implement this
        return False

    def start_turn(self) -> None:
        self.turn_done = False
        self.action_economy.restore_all()
        self._try_expire_effects(is_start=True)

    def end_turn(self) -> None:
        self._try_expire_effects(is_start=False)
        self.turn_done = True

    def end_round(self) -> None:
        pass

    def try_apply_status(self, effect: StatusEffect) -> bool:
        """Apply status effect in case there are no immunities and save throw fails."""
        # Check immunity
        if self.is_immune_to(effect.type):
            self.log_event(f"{self.name} is immune to {effect.type.value} effect")
            return False

        # Saving throw
        if effect.save_dc:
            roll = self.save_roll(save_stat=effect.save_stat)
            self.log_event(f"{effect.save_stat.name} save throw: {roll.total} vs DC {effect.save_dc}", icon=Icon.ROLL)

            if roll.total >= effect.save_dc:
                # Negate effect
                self.log_event(f"{self.name} resists being {effect.type.value}!", icon=Icon.DEFENSE)
                return False

        # Apply the effect
        self.apply_status(effect)

        return True

    def apply_status(self, effect: StatusEffect) -> None:
        """Apply status effect, overriding any ongoing status effect of same type."""
        existing_effect = next((eff for eff in self.status_effects if eff.type == effect.type), None)

        if not existing_effect:
            # No existing effect → just apply it
            self.status_effects.append(effect)
            effect.on_apply(self)
            self.log_event(f"{self.name} is {effect}", icon=Icon.EFFECT_APPLIED)
            return

        # There is already an effect of this type -> remove old one, apply new
        existing_effect.on_expire(self)
        self.status_effects.remove(existing_effect)
        self.status_effects.append(effect)
        effect.on_apply(self)
        self.log_event(f"{self.name} is again {effect}", icon=Icon.EFFECT_APPLIED)

    def _try_expire_effects(self, *, is_start: bool = True) -> None:
        # Copy the list since effects may modify self.status_effects in-place
        for effect in list(self.status_effects):
            effect.on_turn_start(self) if is_start else effect.on_turn_end(self)
            if effect.is_expired():
                effect.on_expire(self)
                self.log_event(f"{self.name} is not {effect.type.value} anymore!", icon=Icon.EFFECT_EXPIRED)

        # Remove expired effects
        self.status_effects = [e for e in self.status_effects if not e.is_expired()]

    def modify_incoming_damage(self, damage: Damage) -> Damage:
        """Apply resistances and vulnerabilities to damage."""
        for dtype in {c.type for c in damage.components}:
            if res := self.attributes.compute_resistance(dtype):
                damage.resistances.append(res)
            if vul := self.attributes.compute_vulnerability(dtype):
                damage.vulnerabilities.append(vul)
        return damage

    def has_resources(self) -> bool:
        has_bonus = self.off_hand is not None and (self.action_economy.bonus_actions > 0)
        main_hand = self.main_hand or self.ranged or self.spells
        has_main = main_hand is not None and (self.action_economy.standard_actions > 0)
        has_movement = self.action_economy.movement_available
        return has_main or has_bonus or has_movement

    def available_actions(self) -> dict[str, Action]:
        all_actions: list[Action] = [
            MovementAction(range=self.current_speed),
            DashAction(range=self.current_speed),
            DodgeAction(),
            WaitAction(),
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
                if isinstance(spell, AttackSpell):
                    action = AttackSpellAction.from_spell(spell)
                elif isinstance(spell, SupportSpell):
                    action = SupportSpellAction.from_spell(spell)
                else:
                    raise NotImplementedError

                all_actions.append(action)

        # Special abilities (can have their own categories)
        all_actions += self.special_abilities

        return {action.id: action for action in all_actions if action.is_available(self.action_economy)}

    def distance(self, target: Position) -> float:
        return self.pos.manhattan_distance(target)

    def initiative_roll(self) -> DiceRoll:
        expr = f"1d20+{self.initiative_modifier}"
        roll = self._dice.roll_with_context(dice_expression=expr)
        self.log_event(f"{self.name} rolls initiative {roll.total}", event_type=EventType.MAIN)
        return roll

    def attack_roll(self, attack_stat: StatType, target: Self) -> DiceRoll:
        # Compute advantage from multiple sources
        sources = [
            self.stats.advantage(attack_stat),
            self.attributes.compute_advantage("attack"),
            target.attributes.compute_advantage("defense"),
        ]
        advantage = resolve_advantage(sources)

        return self._dice.roll_with_context(dice_expression="1d20", advantage=advantage)

    def damage_roll(self, *, expr: str, is_critical: bool = False) -> DiceRoll:
        if is_critical:
            return self._dice.roll_twice(expr)
        return self._dice.roll_once(expr)

    def save_roll(self, save_stat: StatType) -> DiceRoll:
        """
        Rolls a saving throw for the given ability type.
        Accounts for modifiers, proficiency, and active status effects.
        """
        if self.attributes.compute_save_autofail(save_stat):
            return DiceRoll(expression="1d20", rolls=[1], total=1, raw=1)

        # Compute advantage from multiple sources
        sources = [self.stats.advantage(save_stat), self.attributes.compute_save_advantage(save_stat)]
        advantage = resolve_advantage(sources)

        # Roll the d20 (with advantage/disadvantage if applicable)
        ability_mod = self.stats.modifier(save_stat)
        prof_bonus = self.proficiency_bonus if save_stat in self.proficient_saves else 0
        mod = ability_mod + prof_bonus
        expr = f"1d20+{mod}"
        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def add_modifier(self, modifier: Modifier) -> None:
        self.attributes.add_modifier(modifier)

    def remove_modifier(self, source_id: str) -> None:
        self.attributes.remove_modifier(source_id)

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
