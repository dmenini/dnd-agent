def resolve_advantage(sources: list[bool | None]) -> bool | None:
    """
    Resolve multiple advantage/disadvantage sources into a final state.

    Returns True for advantage, False for disadvantage, or None for neutral.
    """
    results = [r for r in sources if r is not None]
    if results:
        return sum(results) > len(sources) / 2
    return None
