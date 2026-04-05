"""Resolution strategies for composable actions.

Resolution strategies determine how an action succeeds or fails:
- AttackRollStrategy: Roll d20 + mods vs target AC
- SavingThrowStrategy: Target rolls save vs caster DC
- AutoSuccessStrategy: Always succeeds (buffs, healing, utility)
"""

from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.saving_throw import SavingThrowStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy

__all__ = [
    "AttackRollStrategy",
    "SavingThrowStrategy",
    "AutoSuccessStrategy",
]
