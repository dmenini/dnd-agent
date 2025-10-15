def resolve_advantage(sources: list[int]) -> bool | None:
    """
    Resolve multiple advantage/disadvantage sources into a final state.

    Returns True for advantage, False for disadvantage, or None for neutral.
    """
    return None if sum(sources) == 0 else sum(sources) > 0
