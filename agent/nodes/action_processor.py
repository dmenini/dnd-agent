from logging import getLogger

from agent.models.state import State

ATTACK_ROLL_EXPR = "1d20"

log = getLogger(__name__)


class ActionProcessorNode:
    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if not state.action or not state.decision:
            return state

        decision = state.decision
        action = state.action
        actor = state.current_actor

        if not actor.is_alive:
            return state

        # Handle the main combat actions
        if decision.target_hits:
            for target_id, hit_count in decision.target_hits.items():
                target = state.characters[target_id]
                if not target:
                    continue

                for i in range(hit_count):
                    actor.log_event(
                        f"{actor.name} performs {action.name} (hit {i + 1}/{hit_count}) on {target.name}."
                    )
                    action.execute(actor=actor, target=target)

        elif decision.target_position is not None:
            actor.log_event(f"{actor.name} performs {action.name} to position {decision.target_position}.")
            action.execute(actor=actor, target=decision.target_position)

        else:
            actor.log_event(f"{actor.name} performs {action.name} on self.")
            action.execute(actor=actor, target=actor)

        action.finalize(actor)

        return state
