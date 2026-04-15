"""
Chapter 03 - The World Engine

The World Engine is the deterministic heart of the simulation.
It's NOT an AI — it's pure Python logic that applies consequences.

Each tick it:
1. Applies natural resource changes (food consumed by population)
2. Introduces random environmental events (droughts, plagues, good harvests)
3. Updates stability based on resource levels
4. Checks for civilizational collapse

This separation matters: the AI (Sovereign) reasons about a world
that has its own rules. The rules don't care about the AI's intentions.
"""

import random
from chapter_02.world_state import WorldState


# How much food each person consumes per year
FOOD_PER_PERSON = 0.4

# Probability of a random event occurring each tick
EVENT_PROBABILITY = 0.25


# Random events that can occur. Each is a tuple of:
# (description, food_delta, stability_delta)
EVENTS = [
    ("A harsh drought withers the crops", -800, -0.08),
    ("Flooding destroys eastern farmland", -600, -0.06),
    ("A plague spreads through the cities", -200, -0.12),
    ("Bandits raid the grain stores", -400, -0.05),
    ("A bountiful harvest fills the granaries", +900, +0.05),
    ("Trade caravans arrive with surplus goods", +500, +0.04),
    ("A period of unusual calm and prosperity", 0, +0.08),
    ("Political unrest in the outer provinces", 0, -0.07),
    ("A great festival unites the people", 0, +0.06),
    ("Discovery of fertile land to the north", +300, +0.03),
]


def world_engine_node(state: WorldState) -> dict:
    """
    The World Engine node.

    Called at the START of each tick, before the Sovereign thinks.
    Applies natural changes and random events to the world.
    """
    updates = {}
    log_entries = []

    # ── 1. Natural resource consumption ───────────────────────────────────────
    food_consumed = int(state["population"] * FOOD_PER_PERSON)
    new_food = state["food_supply"] - food_consumed

    # ── 2. Random event ───────────────────────────────────────────────────────
    event_description = None
    food_delta = 0
    stability_delta = 0

    if random.random() < EVENT_PROBABILITY:
        event_description, food_delta, stability_delta = random.choice(EVENTS)
        new_food += food_delta
        log_entries.append(f"Year {state['year']}: EVENT — {event_description}.")

    # ── 3. Stability adjusts based on food security ───────────────────────────
    # If food supply is critically low, stability drops
    # If food supply is comfortable, stability slowly recovers
    food_ratio = new_food / max(state["population"], 1)  # food per person

    if food_ratio < 0.2:
        # Famine conditions
        stability_delta -= 0.15
        log_entries.append(f"Year {state['year']}: FAMINE — population starving, unrest spreads.")
    elif food_ratio < 0.5:
        # Shortage
        stability_delta -= 0.05
    elif food_ratio > 1.0:
        # Surplus — slight stability boost
        stability_delta += 0.02

    new_stability = max(0.0, min(1.0, state["stability"] + stability_delta))

    # ── 4. Population changes ─────────────────────────────────────────────────
    # Population grows slowly when stable, shrinks in crisis
    if new_stability > 0.6 and new_food > state["population"] * 0.5:
        pop_change = int(state["population"] * 0.02)  # 2% growth
    elif new_stability < 0.2:
        pop_change = -int(state["population"] * 0.05)  # 5% decline in crisis
    else:
        pop_change = 0

    new_population = max(100, state["population"] + pop_change)

    # ── 5. Check for collapse ─────────────────────────────────────────────────
    if new_stability <= 0.05:
        log_entries.append(
            f"Year {state['year']}: COLLAPSE — the civilization fractures. "
            f"The throne is abandoned. The Architect is... pleased."
        )

    # ── Build the update ──────────────────────────────────────────────────────
    updates["food_supply"] = max(0, new_food)
    updates["stability"] = new_stability
    updates["population"] = new_population
    updates["log"] = log_entries

    return updates


def apply_decision_node(state: WorldState) -> dict:
    """
    Translates the Sovereign's decision into mechanical state changes.

    This is a simplified version — in later chapters we'll use an AI
    to parse the decision and apply more nuanced effects.

    For now: decisions that mention certain keywords trigger effects.
    """
    decision = state["sovereign_last_decision"].lower()
    log_entries = []
    food_delta = 0
    stability_delta = 0

    # Simple keyword matching to apply decision effects
    if any(word in decision for word in ["agriculture", "farm", "harvest", "food", "grain"]):
        food_delta += 300
        log_entries.append(f"Year {state['year']}: Agricultural focus yields extra food.")

    if any(word in decision for word in ["military", "army", "soldiers", "fortif"]):
        stability_delta += 0.05
        food_delta -= 100  # military costs resources
        log_entries.append(f"Year {state['year']}: Military investment stabilizes borders.")

    if any(word in decision for word in ["trade", "merchant", "market", "commerce"]):
        food_delta += 200
        stability_delta += 0.03
        log_entries.append(f"Year {state['year']}: Trade routes bring wealth and goods.")

    if any(word in decision for word in ["censor", "control", "suppress", "authoritar", "order"]):
        stability_delta += 0.08  # short term: stability rises
        # Note: in Chapter 05 this will have long-term negative consequences
        log_entries.append(f"Year {state['year']}: Authoritarian measures enforce order.")

    # Increment the year for the next tick
    updates = {
        "year": state["year"] + 1,
        "food_supply": max(0, state["food_supply"] + food_delta),
        "stability": max(0.0, min(1.0, state["stability"] + stability_delta)),
        "log": log_entries,
    }

    return updates
