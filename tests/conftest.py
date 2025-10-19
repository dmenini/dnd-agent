from unittest.mock import MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.config import AgentConfig, LLMConfig, PromptsConfig
from agent.models.state import DecisionResult, State
from agent.nodes.combat_engine import CombatEngineNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode


@pytest.fixture
def config() -> AgentConfig:
    """Mocked config with fake LLM setup."""
    return AgentConfig(
        llm=LLMConfig(name="fake", temperature=0),
        prompts=PromptsConfig(system="You are a decision-making combat AI."),
        retries=1,
    )


@pytest.fixture
def fake_llm(mocker: MockerFixture) -> BaseChatModel:
    """A fake LLM that always returns a fixed decision."""
    llm = mocker.MagicMock(stub=BaseChatModel)
    llm.with_structured_output.return_value = llm
    return llm


def advance_turn(state: State, result: DecisionResult, roll_results: list[int] | None = None) -> State:
    llm = MagicMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = result

    dice = MagicMock(spec=DiceRoller)  # fail save
    roll_results = roll_results or [19]
    rolls = [DiceRoll(expression="1d20", rolls=[], total=result, raw=result) for result in roll_results]
    crit_rolls = [DiceRoll(expression="1d20", rolls=[], total=result * 2, raw=result * 2) for result in roll_results]

    dice.roll_once.side_effect = rolls
    dice.roll_twice.side_effect = crit_rolls
    dice.roll_with_context.side_effect = rolls

    state = DecisionNode(llm=llm, system_prompt="")(state)
    state = CombatEngineNode(dice=dice)(state)
    return EndCombatNode()(state)
