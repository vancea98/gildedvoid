"""
Chapter 02 - World State Definition

This file defines the "ground truth" of our simulation world.
Every agent reads from this state and writes updates back to it.

The TypedDict approach gives us:
- Clear documentation of what fields exist
- Type hints that help catch bugs
- LangGraph-compatible state merging
"""

import operator
from typing import TypedDict, Annotated


class WorldState(TypedDict):
    """
    The complete state of the simulated world at any point in time.

    LangGraph reads this on every tick and passes it to each node.
    Nodes return partial updates — only the fields they changed.
    """

    # ── Time ──────────────────────────────────────────────────────────────────
    year: int
    # The current simulation year. Starts at 1, increments each tick.

    # ── Civilization Resources ─────────────────────────────────────────────────
    population: int
    # Number of people in the civilization. Can grow or collapse.

    food_supply: int
    # Available food units. If this hits 0, famine begins.

    stability: float
    # A value from 0.0 (total collapse) to 1.0 (perfect order).
    # Most civilizations hover around 0.5-0.7 in normal times.

    # ── The Sovereign's Mind ───────────────────────────────────────────────────
    sovereign_ideology: str
    # A short description of the ruling ideology.
    # Starts as "pragmatic democracy" but can drift toward authoritarianism
    # under enough pressure. This is the Semantic Drift in action.

    sovereign_last_decision: str
    # The most recent decision made by the Sovereign agent.
    # Empty string on the first tick.

    # ── The Historical Log ─────────────────────────────────────────────────────
    # Annotated[list[str], operator.add] means:
    # "when two states are merged, ADD the lists together (append)"
    # instead of replacing one list with the other.
    # This way every node can add entries without losing previous ones.
    log: Annotated[list[str], operator.add]


def create_initial_state() -> WorldState:
    """
    Returns the starting world state for a fresh simulation.
    This is "Year 1" — before the Architect has done anything.
    """
    return WorldState(
        year=1,
        population=10000,
        food_supply=5000,
        stability=0.75,
        sovereign_ideology="pragmatic democracy — collective welfare above all",
        sovereign_last_decision="",
        log=["Year 1: A new civilization awakens. The throne stands empty. The Architect watches."],
    )
