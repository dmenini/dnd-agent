from enum import Enum

from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.ai.components import create_llm
from agent.mechanics.dice_roller import DiceRoller
from agent.models.config import AgentConfig
from agent.models.state import State
from agent.nodes.action_processor import ActionProcessorNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode
from agent.nodes.rules_verifier import RulesVerifierNode
from agent.nodes.start_combat import StartCombatNode


class TurnPhase(str, Enum):
    DECIDE = "decide"
    VERIFY = "verify"
    ROLL = "roll"
    EXECUTE = "execute"
    START = "start"
    END = "end"


def is_valid_action(state: State) -> str:
    if state.verification_result and state.verification_result.valid:
        return TurnPhase.EXECUTE

    return TurnPhase.DECIDE  # re-evaluate action


def build_graph(config: AgentConfig) -> CompiledStateGraph:
    graph = StateGraph(state_schema=State)
    llm = create_llm(config.llm)

    # Nodes
    agent = DecisionNode(llm=llm, system_prompt=config.prompts.system, **config.decision_node)
    verifier = RulesVerifierNode()
    start_combat = StartCombatNode(dice=DiceRoller())
    combat = ActionProcessorNode()
    end_combat = EndCombatNode()

    # Register nodes
    graph.add_node(TurnPhase.START, start_combat)
    graph.add_node(TurnPhase.DECIDE, agent)
    graph.add_node(TurnPhase.VERIFY, verifier)
    graph.add_node(TurnPhase.EXECUTE, combat)
    graph.add_node(TurnPhase.END, end_combat)

    # Define edges
    graph.add_edge(START, TurnPhase.START)
    graph.add_edge(TurnPhase.START, TurnPhase.DECIDE)
    graph.add_edge(TurnPhase.DECIDE, TurnPhase.VERIFY)
    graph.add_conditional_edges(TurnPhase.VERIFY, is_valid_action)
    graph.add_edge(TurnPhase.EXECUTE, TurnPhase.END)

    return graph.compile()
