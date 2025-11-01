from agent.actions.common.wait import WaitAction
from agent.character.character import Character
from agent.models.decision import DecisionResult
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State, VerificationResult


def test_serialization(actor: Character, game_map: GameMap) -> None:
    state = State(
        round=0,
        turn_index=0,
        map=game_map,
        characters={actor.id: actor},
        parties={actor.party.id: actor.party},
        decision=DecisionResult(
            action_id="wait",
            target_hits={"test": 1},
            target_position=Position(x=1, y=1, direction="N"),
            description="lorem ipsum",
        ),
        verification_result=VerificationResult(valid=True, reason="something", input=WaitAction()),
        done=False,
        retries=0,
        command="",
    )
    state_dict = state.model_dump()
    state2 = State.model_validate(state_dict)

    assert state.model_dump() == state2.model_dump()
