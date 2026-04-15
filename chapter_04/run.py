"""
Chapter 04 - Simulation with Ancestral Memory

Extends Chapter 03 with:
- Civilization collapse detection triggering the Great Reset
- ChromaDB storage of collapsed civilizations
- Ancestral trauma injection into new civilizations

Usage:
  python -m chapter_04.run                    ← resume or start
  python -m chapter_04.run --reset            ← wipe simulation, keep memories
  python -m chapter_04.run --reset --wipe-memory  ← wipe everything
"""

import sys
import time
import os
import argparse

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from chapter_02.world_state import WorldState, create_initial_state
from chapter_02.first_agent import sovereign_node, build_sovereign_prompt, MODEL
from chapter_03.world_engine import world_engine_node, apply_decision_node
from chapter_04.great_reset import great_reset
from chapter_04.memory_store import get_trauma, format_trauma_for_prompt

import ollama


DB_PATH = "simulation.db"
TICK_DELAY = 2.0
THREAD_ID = "gilded_void_timeline_1"


def sovereign_node_with_memory(state: WorldState) -> dict:
    """
    Enhanced Sovereign node that includes ancestral memory in its prompt.

    Replaces the plain sovereign_node from Chapter 02.
    The only difference: we query ChromaDB for relevant memories
    and inject them into the prompt before calling the model.
    """
    # Build the base prompt
    base_prompt = build_sovereign_prompt(state)

    # Query ancestral memory for anything relevant to the current situation
    current_situation = (
        f"civilization with stability {state['stability']:.0%}, "
        f"food supply {state['food_supply']}, "
        f"ideology: {state['sovereign_ideology'][:50]}"
    )
    memories = get_trauma(current_situation, n_results=2)
    trauma_text = format_trauma_for_prompt(memories)

    # Inject memories into the prompt if we have any
    if trauma_text:
        full_prompt = f"{trauma_text}\n{base_prompt}"
    else:
        full_prompt = base_prompt

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": full_prompt}],
    )
    decision = response["message"]["content"].strip()

    return {
        "sovereign_last_decision": decision,
        "log": [f"Year {state['year']}: Sovereign decrees — \"{decision}\""],
    }


def should_continue(state: WorldState) -> str:
    """
    Routing function. On collapse, returns 'collapse' instead of looping.
    """
    if state["stability"] <= 0.05:
        return "collapse"
    return "world_engine"


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
        {
            "world_engine": "world_engine",
            "collapse": END,
        },
    )

    return builder.compile(checkpointer=checkpointer)


def print_tick_summary(state: WorldState):
    stability_bar = "█" * int(state["stability"] * 20) + "░" * (20 - int(state["stability"] * 20))
    print(f"\n{'─' * 60}")
    print(f"  YEAR {state['year']:>4}  │  Pop: {state['population']:>7,}  │  Food: {state['food_supply']:>7,}")
    print(f"  Stability [{stability_bar}] {state['stability']:.0%}")
    print(f"  Decision: {state['sovereign_last_decision'][:55]}")
    for entry in state["log"][-2:]:
        print(f"  › {entry}")


def run_simulation(checkpointer, input_state):
    """Runs one full civilization until collapse or keyboard interrupt."""
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": THREAD_ID}}

    for state_update in graph.stream(input_state, config=config, stream_mode="values"):
        print_tick_summary(state_update)
        time.sleep(TICK_DELAY)

    # Return the final state after the loop ends
    final = graph.get_state(config)
    return final.values if final.values else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Wipe simulation save")
    parser.add_argument("--wipe-memory", action="store_true", help="Also wipe ancestral memory")
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
    print("Press Ctrl+C to pause at any time.")
    print("=" * 60)

    # The outer loop handles Great Resets — each iteration is one civilization
    era = 1
    current_input = None  # None = resume from checkpoint if it exists

    try:
        while True:
            print(f"\n[ERA {era}] Civilization begins...")

            with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
                # Check for existing save on first era
                if era == 1 and current_input is None:
                    graph = build_graph(checkpointer)
                    config = {"configurable": {"thread_id": THREAD_ID}}
                    existing = graph.get_state(config)
                    if existing.values:
                        year = existing.values.get("year", "?")
                        print(f"[RESUME] Found save at Year {year}. Continuing...")
                        current_input = None
                    else:
                        current_input = create_initial_state()

                final_state = run_simulation(checkpointer, current_input)

            if final_state and final_state.get("stability", 1.0) <= 0.05:
                # Civilization collapsed — run the Great Reset
                current_input = great_reset(final_state)
                # Wipe the simulation DB so the new era starts fresh
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                era += 1
            else:
                # Simulation was paused by user (Ctrl+C)
                break

    except KeyboardInterrupt:
        print("\n\n[PAUSED] Simulation paused. Run again to resume.")


if __name__ == "__main__":
    main()
