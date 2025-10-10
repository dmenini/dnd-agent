import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from agent.models.state import Action, Context, Observation, State


class LLMAgent:
    def __init__(self, llm: BaseChatModel, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state: State, runtime: Runtime[Context]) -> State:
        user_prompt = f"Observation: {state.observation.model_dump_json(indent=2)}"
        result = self.llm.invoke([SystemMessage(content=self.system_prompt), HumanMessage(content=user_prompt),])

        try:
            parsed = json.loads(result.content)
            state.action = Action(**parsed)
            return state
        except Exception as e:
            print("Parsing failed:", e, result.content)
            state.action = Action(actor_id="pc_alfred", action_type="wait", description="waits for a moment.")
            return state
