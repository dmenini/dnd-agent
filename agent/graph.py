from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.mechanics.dice_roller import DiceRoller
from agent.models.config import AgentConfig, LLMConfig
from agent.models.enums import TurnPhase
from agent.models.state import Context, State
from agent.nodes.combat_engine import CombatEngineNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode
from agent.nodes.rules_verifier import RulesVerifierNode
from agent.nodes.start_combat import StartCombatNode


def create_llm(config: LLMConfig) -> BaseChatModel:
    # Converse API: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
    return ChatBedrockConverse(
        model=config.name,
        temperature=config.temperature,
    )


def should_continue(state: State) -> str:
    if state.done:
        return END
    return TurnPhase.DECIDE


def build_graph(config: AgentConfig) -> CompiledStateGraph:
    graph = StateGraph(state_schema=State)
    llm = create_llm(config.llm)

    # Nodes
    agent = DecisionNode(llm=llm, system_prompt=config.prompts.system)
    verifier = RulesVerifierNode()
    start_combat = StartCombatNode(dice=DiceRoller())
    combat = CombatEngineNode(dice=DiceRoller())
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
    graph.add_edge(TurnPhase.VERIFY, TurnPhase.EXECUTE)
    graph.add_edge(TurnPhase.EXECUTE, TurnPhase.END)
    graph.add_conditional_edges(TurnPhase.END, should_continue)

    return graph.compile()
