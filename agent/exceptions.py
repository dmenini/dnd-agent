class GameBackendError(Exception):
    """Base exception for GameBackend errors."""


class InvalidPhaseError(GameBackendError):
    """Raised when an operation is attempted in the wrong phase."""


class CharacterCreationError(GameBackendError):
    """Raised when character creation fails."""
