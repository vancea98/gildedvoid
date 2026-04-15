"""
Chapter 04 - Simulation with Ancestral Memory

Single civilization, persistent memory across Great Resets.
New concepts introduced here: ChromaDB, semantic trauma, the Great Reset loop.

Usage:
  python -m chapter_04.run
  python -m chapter_04.run --reset            ← wipe simulation, keep memories
  python -m chapter_04.run --reset --wipe-memory  ← wipe everything
"""

import time
import os
import argparse

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from chapter_02.world_state import WorldState, create_initial_state
from chapter_03.world_engine import world_engine_node, apply_decision_node
from chapter_04.nodes import sovereign_node_with_memory
from chapter_04.great_reset import great_reset


DB_PATH = "simulation.db"
TICK_DELAY = 2.0
THREAD_ID = "gilded_void_timeline_1"


def should_continue(state: WorldState) -> str:
    return "collapse" if state["stability"] <= 0.05 else "world_engine"


def build_graph(checkpointer):
    builder = StateGraph(WorldState)
    builder.add_node("world_engine", world_engine_node)
    builder.add_node("sovereign", sovereign_node_with_memory)
    builder.add_node("apply_decision", apply_decision_node)
    builder.set_entry_point("world_engine")
    builder.add_edge("world_engine", "sovereign")
    builder.add_edge("sovereign", "apply_decision")
    builder.add_conditional_edges(
        "apply_decision",
        should_continue,
        {"world_engine": "world_engine", "collapse": END},
    )
    return builder.compile(checkpointer=checkpointer)


def print_tick(state: WorldState):
    bar = "█" * int(state["stability"] * 20) + "░" * (20 - int(state["stability"] * 20))
    print(f"\n{'─' * 60}")
    print(f"  YEAR {state['year']:>4}  │  Pop: {state['population']:>7,}  │  Food: {state['food_supply']:>7,}")
    print(f"  Stability [{bar}] {state['stability']:.0%}")
    print(f"  Decision: {state['sovereign_last_decision'][:55]}")
    for entry in state["log"][-2:]:
        print(f"  › {entry}")


def run_era(checkpointer, input_state) -> dict:
    """Runs one civilization era until collapse or Ctrl+C. Returns final state."""
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": THREAD_ID}}
    for state_update in graph.stream(input_state, config=config, stream_mode="values"):
        print_tick(state_update)
        time.sleep(TICK_DELAY)
    final = graph.get_state(config)
    return final.values if final.values else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--wipe-memory", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[RESET] Simulation save wiped.")
    if args.wipe_memory:
        from chapter_04.memory_store import wipe_memories
        wipe_memories()

    print("=" * 60)
    print("The Gilded Void — Chapter 04: Ancestral Memory")
    print("=" * 60)

    era = 1
    current_input = None

    try:
        while True:
            print(f"\n[ERA {era}] Civilization begins...")

            with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
                if era == 1 and current_input is None:
                    graph = build_graph(checkpointer)
                    config = {"configurable": {"thread_id": THREAD_ID}}
                    existing = graph.get_state(config)
                    if existing.values:
                        print(f"[RESUME] Found save at Year {existing.values.get('year', '?')}.")
                        current_input = None
                    else:
                        current_input = create_initial_state()

                final_state = run_era(checkpointer, current_input)

            if final_state.get("stability", 1.0) <= 0.05:
                current_input = great_reset(final_state)
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                era += 1
            else:
                break

    except KeyboardInterrupt:
        print("\n[PAUSED] Simulation paused. Run again to resume.")


if __name__ == "__main__":
    main()
