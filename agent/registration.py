from agent.actions.jobs.fighter import SecondWindAction
from agent.actions.registry import ActionRegistry
from agent.effects.registry import TraitRegistry
from agent.effects.traits import ACBonusWithArmor
from agent.models.constants import FeatureId


def register_actions() -> None:
    ActionRegistry.register(FeatureId.SECOND_WIND_ID, SecondWindAction)


def register_traits() -> None:
    TraitRegistry.register(FeatureId.FIGHTING_STYLE_DEFENSE, ACBonusWithArmor)
