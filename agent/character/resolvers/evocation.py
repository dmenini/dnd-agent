from agent.actions.base import Action
from agent.character.resolvers.base import CharacterBase
from agent.effects.evocations.base import Evocation


class EvocationResolver(CharacterBase):
    evocations: list[Evocation] = []

    def add_evocation(self, evo: Evocation) -> None:
        existing = next((e for e in self.evocations if e.source_id == evo.source_id), None)

        if not existing:
            self.evocations.append(evo)
            return

        # There is already an evocation of this type → remove old one, apply new
        self.remove_evocation(evo.source_id)
        self.evocations.append(evo)

    def remove_evocation(self, source_id: str) -> None:
        self.evocations = [e for e in self.evocations if e.source_id != source_id]

    def expire_evocations(self) -> None:
        for evo in list(self.evocations):
            evo.duration -= 1
            evo.action_economy.restore_turn()
            if evo.is_expired():
                self.remove_evocation(evo.source_id)

    def evocation_actions(self) -> list[Action]:
        actions = []
        for evo in self.evocations:
            actions.extend(evo.available_actions())
        return actions
