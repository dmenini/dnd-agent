from enum import Enum

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from agent.ai.components import create_llm
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
    start_combat = StartCombatNode()
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

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


async def run_interrupt_loop(state: State, graph: CompiledStateGraph) -> None:
    started = False
    print("Press ENTER to start game...")
    while True:
        command = input()

        config = RunnableConfig(recursion_limit=20, configurable={"thread_id": "thread-1"})

        # First run - start the graph
        if not started:
            result = await graph.ainvoke(state, config)
            started = True

        # User responded - resume last interrupt
        else:
            # Resume the last interrupt (continues thread)
            result = await graph.ainvoke(Command(resume=command), config)
            state = State.model_validate(result)

            # Immediately continue execution until the next interrupt
            result = await graph.ainvoke(state, config)

        state = State.model_validate(result)

        # If new interrupt, update UI placeholder
        if intr := result.get("__interrupt__"):
            print(intr[0].value)
