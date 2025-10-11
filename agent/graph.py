from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.models.config import AgentConfig, LLMConfig
from agent.models.state import Context, State
from agent.nodes.agent import NpcNode
from agent.nodes.combat_engine import CombatEngineNode
from agent.nodes.dice_roller import DiceRoller
from agent.nodes.rules_verifier import RulesVerifierNode


def create_llm(config: LLMConfig) -> BaseChatModel:
    # Converse API: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
    return ChatBedrockConverse(
        model=config.name,
        temperature=config.temperature,
    )


def build_graph(config: AgentConfig) -> CompiledStateGraph:
    graph = StateGraph(state_schema=State, context_schema=Context)
    llm = create_llm(config.llm)

    # Nodes
    agent = NpcNode(llm=llm, system_prompt=config.prompts.system)
    verifier = RulesVerifierNode()
    combat = CombatEngineNode(dice=DiceRoller())

    # Register nodes
    graph.add_node("decide", agent)
    graph.add_node("verify", verifier)
    graph.add_node("execute", combat)

    # Define edges
    graph.add_edge(START, "decide")
    graph.add_edge("decide", "verify")
    graph.add_edge("verify", "execute")
    graph.add_edge("execute", END)

    return graph.compile()
