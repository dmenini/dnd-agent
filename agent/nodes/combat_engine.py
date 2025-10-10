from langgraph.runtime import Runtime

from agent.models.state import Action, ActionType, CombatResult, Context, State, TurnPhase


class CombatEngine:
    def __call__(self, state: State, runtime: Runtime[Context]) -> State:
        action = state.action
        roll = state.roll
        actor = state.characters.get(state.actor_id)
        target = state.characters.get(action.target_id) if action else None

        event = f"{action.actor_id} performs {action.action_type} ({action.description or ''})"

        if action.action_type == ActionType.ATTACK and roll.total:
            event += f" and rolls {roll.total}!"
            if roll.total >= 12 and target:
                target.hp -= 5
                event += f" Hits {target.name} for 5 damage (HP now {target.hp})."
                if target.hp <= 0:
                    event += f" {target.name} is defeated!"
                    target.hp = 0

        state.event_log.append(event)
        state.phase = TurnPhase.DECIDE
        state.turn += 1

        if all(c.hp <= 0 for c in state.characters.values() if not c.is_player):
            state.done = True

        return state
