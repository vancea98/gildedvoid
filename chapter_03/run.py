"""
Chapter 03 - The Infinite Simulation Loop

This script runs the simulation continuously, saving state to disk
so it survives reboots and crashes.

Usage:
  python -m chapter_03.run          ← resume or start fresh
  python -m chapter_03.run --reset  ← wipe save and start over
"""

import sys
import time
import os
import argparse

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver  # requires: pip install langgraph-checkpoint-sqlite

from chapter_02.world_state import WorldState, create_initial_state
from chapter_02.first_agent import sovereign_node
from chapter_03.world_engine import world_engine_node, apply_decision_node


# Where the simulation state is saved between runs
DB_PATH = "simulation.db"

# How long to pause between ticks (seconds)
# Lower = faster simulation, higher = more readable output
TICK_DELAY = 2.0

# The thread_id identifies this particular simulation timeline.
# If you wanted multiple parallel simulations, you'd use different thread_ids.
THREAD_ID = "gilded_void_timeline_1"


def should_continue(state: WorldState) -> str:
    """
    Routing function — decides what happens after apply_decision.

    Returns the name of the next node to run, OR the special string END.
    This is how LangGraph implements conditional branching.

    Right now: loop forever unless civilization collapses.
    """
    if state["stability"] <= 0.05:
        print("\n[SIMULATION] Civilization has collapsed. The Architect smiles.")
        return END
    return "world_engine"  # loop back to the start


def build_graph(checkpointer):
    """
    Builds the simulation graph with persistence.

    The checkpointer parameter is the SQLite saver — it automatically
    saves state after every node execution.
    """
    builder = StateGraph(WorldState)

    # Add all three nodes
    builder.add_node("world_engine", world_engine_node)
    builder.add_node("sovereign", sovereign_node)
    builder.add_node("apply_decision", apply_decision_node)

    # Define the flow
    builder.set_entry_point("world_engine")
    builder.add_edge("world_engine", "sovereign")
    builder.add_edge("sovereign", "apply_decision")

    # Conditional edge: after apply_decision, check if we should continue or end
    builder.add_conditional_edges(
        "apply_decision",
        should_continue,
        {
            "world_engine": "world_engine",  # continue looping
            END: END,                          # stop simulation
        },
    )

    # compile() with a checkpointer enables automatic state saving
    return builder.compile(checkpointer=checkpointer)


def print_tick_summary(state: WorldState):
    """Prints a readable summary of the current world state."""
    stability_bar = "█" * int(state["stability"] * 20) + "░" * (20 - int(state["stability"] * 20))

    print(f"\n{'─' * 60}")
    print(f"  YEAR {state['year']:>4}  │  Pop: {state['population']:>7,}  │  Food: {state['food_supply']:>7,}")
    print(f"  Stability [{stability_bar}] {state['stability']:.0%}")
    print(f"  Ideology: {state['sovereign_ideology'][:55]}")
    print(f"  Decision: {state['sovereign_last_decision'][:55]}")

    # Print only the most recent log entries (not the whole history)
    recent = state["log"][-3:]
    for entry in recent:
        print(f"  › {entry}")


def main():
    parser = argparse.ArgumentParser(description="Run The Gilded Void simulation")
    parser.add_argument("--reset", action="store_true", help="Wipe save and start fresh")
    args = parser.parse_args()

    # If --reset flag used, delete the save file
    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[RESET] Deleted {DB_PATH}. Starting fresh.")

    print("=" * 60)
    print("The Gilded Void — Chapter 03: Infinite Loop")
    print("=" * 60)
    print(f"Save file: {DB_PATH}")
    print("Press Ctrl+C to pause. Run again to resume.")
    print("=" * 60)

    # SqliteSaver automatically creates the database file if it doesn't exist
    # It saves a checkpoint after EVERY node execution
    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)

        # config identifies which "thread" (timeline) we're running
        config = {"configurable": {"thread_id": THREAD_ID}}

        # Check if there's an existing save to resume from
        existing_state = graph.get_state(config)
        if existing_state.values:
            year = existing_state.values.get("year", "?")
            print(f"\n[RESUME] Found existing simulation at Year {year}.")
            print("Continuing from checkpoint...\n")
            # Pass None as input — LangGraph will use the checkpointed state
            input_state = None
        else:
            print("\n[NEW] No save found. Starting Year 1...\n")
            input_state = create_initial_state()

        # Run the simulation
        try:
            for state_update in graph.stream(input_state, config=config, stream_mode="values"):
                print_tick_summary(state_update)
                time.sleep(TICK_DELAY)

        except KeyboardInterrupt:
            print("\n\n[PAUSED] Simulation paused. Run again to resume.")
            if existing_state.values or input_state:
                final = graph.get_state(config)
                if final.values:
                    print(f"[SAVED] State saved at Year {final.values.get('year', '?')}.")


if __name__ == "__main__":
    main()
