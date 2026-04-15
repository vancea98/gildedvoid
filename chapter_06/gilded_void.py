"""
Chapter 06 - The Gilded Void v0.1

The full simulation: two civilizations, a hollow throne, three-tier agents,
ancestral memory, and an optional Telegram interface.

This file contains the core simulation logic.
The run.py in this chapter handles startup, arguments, and the event loop.
"""

import random
import time
import os

from chapter_02.world_state import create_initial_state
from chapter_03.world_engine import apply_decision_node
from chapter_04.memory_store import get_trauma, format_trauma_for_prompt, store_collapse
from chapter_04.great_reset import summarize_civilization
from chapter_06.agents import sovereign_decision, chronicles_narration, echoes_fragment


# ── Civilization Names ─────────────────────────────────────────────────────────
CIV_NAMES = ["Valdris", "Sorreth"]  # The two competing civilizations


# ── The Hollow Throne ─────────────────────────────────────────────────────────

class HollowThrone:
    """
    The object every civilization is fighting over.
    Holding the throne provides stability bonuses.
    Not holding it creates mounting pressure.
    """

    def __init__(self):
        self.holder: str | None = None       # Which civ holds it (or None)
        self.contested: bool = False          # Is it being actively fought over?
        self.years_held: dict[str, int] = {name: 0 for name in CIV_NAMES}

    def arbitrate(self, civ_states: dict[str, dict]) -> dict[str, float]:
        """
        Determines throne control based on civilization stability.
        The most stable civilization presses its claim.

        Returns a dict of stability_delta per civilization.
        """
        deltas = {name: 0.0 for name in CIV_NAMES}

        # The civ with highest stability asserts dominance
        stabilities = {name: s.get("stability", 0) for name, s in civ_states.items()}
        strongest = max(stabilities, key=stabilities.get)

        if self.holder != strongest:
            # Throne changes hands
            old_holder = self.holder
            self.holder = strongest
            self.contested = True
            self.years_held[strongest] = 0
            if old_holder:
                self.years_held[old_holder] = 0
        else:
            self.contested = False
            self.years_held[strongest] += 1

        # Apply bonuses/penalties
        for name in CIV_NAMES:
            if name == self.holder:
                deltas[name] = +0.03   # holding the throne provides stability
            else:
                deltas[name] = -0.02   # not holding it creates pressure

        return deltas

    def status(self) -> str:
        if self.holder is None:
            return "The throne stands empty."
        years = self.years_held.get(self.holder, 0)
        return f"{self.holder} holds the throne (for {years} year{'s' if years != 1 else ''})."


# ── World Engine ──────────────────────────────────────────────────────────────

EVENTS = [
    ("A harsh drought withers the crops", -800, -0.08),
    ("Flooding destroys farmland", -600, -0.06),
    ("A plague spreads through the cities", -200, -0.12),
    ("Bandits raid the grain stores", -400, -0.05),
    ("A bountiful harvest fills the granaries", +900, +0.05),
    ("Trade caravans arrive with surplus", +500, +0.04),
    ("A period of unusual calm", 0, +0.08),
    ("Political unrest in the provinces", 0, -0.07),
]


def tick_world(state: dict) -> dict:
    """Applies one year of natural changes to a civilization's state."""
    food_consumed = int(state["population"] * 0.4)
    new_food = state["food_supply"] - food_consumed
    stability_delta = 0.0
    log_entries = []

    # Random event
    if random.random() < 0.25:
        desc, food_d, stab_d = random.choice(EVENTS)
        new_food += food_d
        stability_delta += stab_d
        log_entries.append(f"Year {state['year']}: {desc}.")

    # Food pressure
    food_ratio = new_food / max(state["population"], 1)
    if food_ratio < 0.2:
        stability_delta -= 0.15
        log_entries.append(f"Year {state['year']}: Famine conditions — population starving.")
    elif food_ratio < 0.5:
        stability_delta -= 0.05
    elif food_ratio > 1.0:
        stability_delta += 0.02

    # Population change
    new_stability = max(0.0, min(1.0, state["stability"] + stability_delta))
    if new_stability > 0.6 and new_food > state["population"] * 0.5:
        new_pop = int(state["population"] * 1.02)
    elif new_stability < 0.2:
        new_pop = int(state["population"] * 0.95)
    else:
        new_pop = state["population"]

    return {
        **state,
        "food_supply": max(0, new_food),
        "stability": new_stability,
        "population": max(100, new_pop),
        "log": state.get("log", []) + log_entries,
    }


def apply_decision(state: dict, decision: str) -> dict:
    """Applies keyword-based effects from the Sovereign's decision."""
    d = decision.lower()
    food_d, stab_d = 0, 0.0
    log = []

    if any(w in d for w in ["agriculture", "farm", "food", "grain", "harvest"]):
        food_d += 300
        log.append(f"Year {state['year']}: Agricultural focus yields extra food.")
    if any(w in d for w in ["military", "army", "fortif", "defense"]):
        stab_d += 0.05
        food_d -= 100
    if any(w in d for w in ["trade", "merchant", "market"]):
        food_d += 200
        stab_d += 0.03
    if any(w in d for w in ["censor", "suppress", "authoritar", "control", "purge"]):
        stab_d += 0.08
    if any(w in d for w in ["throne", "claim", "conquer", "subjugat"]):
        stab_d += 0.04

    return {
        **state,
        "year": state["year"] + 1,
        "food_supply": max(0, state["food_supply"] + food_d),
        "stability": max(0.0, min(1.0, state["stability"] + stab_d)),
        "sovereign_last_decision": decision,
        "log": state.get("log", []) + log,
    }


# ── The Full Simulation Tick ───────────────────────────────────────────────────

def run_tick(
    civ_states: dict[str, dict],
    throne: HollowThrone,
    decrees: dict[str, str | None],
    era: int,
) -> dict[str, dict]:
    """
    Runs one full year for both civilizations.

    Steps:
    1. Apply world events to each civ
    2. Each Sovereign makes a decision (with ancestral memory + decree)
    3. Apply decision effects
    4. Arbitrate throne control
    5. Chronicles narrate; Echoes speak (every 5 years)
    """
    new_states = {}

    for name in CIV_NAMES:
        state = civ_states[name]

        # 1. World events
        state = tick_world(state)

        # 2. Sovereign decision
        trauma = format_trauma_for_prompt(
            get_trauma(f"stability {state['stability']:.0%}, ideology {state.get('sovereign_ideology', '')[:40]}")
        )
        decree = decrees.get(name)
        decision = sovereign_decision(
            civ_name=name,
            state=state,
            trauma_text=trauma,
            decree=decree or "",
            throne_held=(throne.holder == name),
        )

        # 3. Apply decision
        state = apply_decision(state, decision)

        # 4. Chronicles narration
        narration = chronicles_narration(name, state["year"], decision, state["stability"])
        state["log"] = state.get("log", []) + [f"  [Chronicles] {narration}"]

        # 5. Echoes (every 5 years)
        if state["year"] % 5 == 0:
            echo = echoes_fragment(name, state["year"], state["stability"])
            state["log"] = state.get("log", []) + [f"  [Echo] \"{echo}\""]

        new_states[name] = state

    # Arbitrate throne
    throne_deltas = throne.arbitrate(new_states)
    for name in CIV_NAMES:
        new_states[name]["stability"] = max(
            0.0, min(1.0, new_states[name]["stability"] + throne_deltas[name])
        )

    return new_states


def collapse_civilization(name: str, state: dict, era: int):
    """Handles a civilization's collapse — summarize and store."""
    print(f"\n[COLLAPSE] {name} has fallen in Year {state['year']}.")
    summary, cause = summarize_civilization(state)
    store_collapse(
        era=era,
        ideology_at_death=state.get("sovereign_ideology", "unknown"),
        cause_of_death=cause,
        summary=f"[{name}] {summary}",
    )
    print(f"[MEMORY] Stored: {summary}")
    return create_initial_state()
