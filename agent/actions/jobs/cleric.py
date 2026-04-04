from agent.actions.base import ActionType, BonusAction, LimitedBonusAction
from agent.actions.common.attack import AttackAction
from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.character.resources import ActionEconomy
from agent.equipment.weapons import WeaponType
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService


class DivineRestorationAction(LimitedBonusAction):
    """Once per combat, channel divine power to heal allies."""

    id: str
    description: str
    name: str = "Divine Restoration"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.MULTI

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        # TODO: Should run on all allies
        heal_roll = RollService.heal_roll(actor, expr="1d10")
        heal_amount = heal_roll.total + actor.level // 2
        heal_amount = min(heal_amount, target.max_hp - target.attributes.hp)
        CombatService.heal(target, heal_amount)
        actor.log_event(
            f"{actor.name} channels divine light to heal {target.name} "
            f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
            log_type=LogLevel.DETAIL,
        )


class WarPriestAction(BonusAction, AttackAction):
    """Make one weapon attack as a bonus action after using the Attack action.

    Uses per rest = Wisdom modifier (minimum 1).
    """

    id: str
    description: str
    name: str = "War Priest"
    type: ActionType = ActionType.ATTACK
    targeting: TargetingType = TargetingType.SINGLE

    uses_per_rest: int = 1
    current_uses: int = 0

    # Attack properties - will be populated from weapon
    damage_dice: str = "1d6"
    damage_type: DamageType = DamageType.BLUDGEONING
    weapon_type: WeaponType = WeaponType.SIMPLE_MELEE
    ability: AbilityType = AbilityType.STR
    range: float = 1.5

    def is_available(self, action_economy: ActionEconomy) -> bool:
        # Must have used Attack action this turn
        if action_economy.last_standard_action != ActionType.ATTACK:
            return False

        # Must have uses remaining
        if self.current_uses >= self.uses_per_rest:
            return False

        # Check if bonus action is available
        return action_economy.can_use_bonus(self.type)

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        # Update attack properties from equipped weapon
        if actor.equipment.main_hand:
            weapon = actor.equipment.main_hand
            self.damage_dice = weapon.damage_dice
            self.damage_type = weapon.damage_type
            self.weapon_type = weapon.weapon_type
            self.range = weapon.range

            # Determine ability (finesse weapons can use DEX or STR)
            if weapon.finesse:
                self.ability = (
                    AbilityType.STR if actor.attributes.strength >= actor.attributes.dexterity else AbilityType.DEX
                )
            else:
                self.ability = weapon.ability

        # Execute using parent AttackAction logic
        super().execute(actor, target, ctx)

    def finalize(self, actor: Character) -> None:
        # Consume bonus action
        actor.action_economy.use_bonus(self.type)
        # Consume use
        self.current_uses += 1

    def rest(self) -> None:
        """Reset uses on long rest."""
        self.current_uses = 0


class PreserveLifeAction(LimitedBonusAction):
    """Restore a number of hit points equal to five times your cleric level.
    Choose any creatures within 30 feet of you, and divide those hit points among them.
    This feature can restore a creature to no more than half of its hit point maximum.
    You can't use this feature on an undead or a construct.
    """

    id: str
    description: str
    name: str = "Preserve Life"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.ALLIES
    range: int = 30

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        total = actor.level * 5
        num_targets = len([val for val in ctx.hits.values() if val > 0])
        heal_amount = min(total // num_targets, target.max_hp // 2, target.max_hp - target.attributes.hp)
        CombatService.heal(target, heal_amount)
        actor.log_event(
            f"{actor.name} channels divine light to heal {target.name} "
            f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
            log_type=LogLevel.DETAIL,
        )
