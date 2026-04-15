"""
Chapter 05 - Telegram Bridge

Adds the Architect's interface to the Chapter 04 simulation.
New concepts here: asyncio, Telegram bot, divine decrees, threshold events.

This module only defines what's NEW compared to Chapter 04:
  - world_engine_with_events()  ← applies Architect-triggered events
  - sovereign_with_decree()     ← injects divine decrees into prompts
  - The async simulation loop that lets bot and sim run concurrently

Everything else (graph structure, memory, Great Reset) is imported from ch04.

Usage:
  python -m chapter_05.run
  python -m chapter_05.run --reset
  python -m chapter_05.run --reset --wipe-memory
"""

import asyncio
import os
import argparse

import ollama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from chapter_02.world_state import WorldState, create_initial_state
from chapter_02.first_agent import build_sovereign_prompt, MODEL
from chapter_03.world_engine import world_engine_node, apply_decision_node
from chapter_04.memory_store import get_trauma, format_trauma_for_prompt
from chapter_04.great_reset import great_reset
from chapter_04.run import print_tick, TICK_DELAY, THREAD_ID, DB_PATH
from chapter_05.telegram_bridge import SimulationContext, build_bot, load_config, send_notification
from chapter_05.threshold_events import check_threshold_events


# ── New nodes for this chapter ────────────────────────────────────────────────

def world_engine_with_events(context: SimulationContext):
    """
    Wraps the standard world_engine node to also apply pending Architect events.
    This is the only change to the world engine — everything else is identical to ch04.
    """
    def node(state: WorldState) -> dict:
        updates = world_engine_node(state)
        event = context.consume_event()
        if event == "famine":
            updates["food_supply"] = max(0, state["food_supply"] - 2000)
            updates["stability"] = max(0.0, state.get("stability", 0.5) - 0.15)
            updates["log"] = updates.get("log", []) + [
                f"Year {state['year']}: DIVINE INTERVENTION — The Architect has decreed famine."
            ]
        elif event == "prosperity":
            updates["food_supply"] = state["food_supply"] + 3000
            updates["stability"] = min(1.0, state.get("stability", 0.5) + 0.10)
            updates["log"] = updates.get("log", []) + [
                f"Year {state['year']}: DIVINE INTERVENTION — The Architect has granted abundance."
            ]
        return updates
    return node


def sovereign_with_decree(context: SimulationContext):
    """
    Wraps the memory-aware Sovereign to also inject any pending divine decree.
    Same as ch04's sovereign_node_with_memory, plus one extra block for decrees.
    """
    def node(state: WorldState) -> dict:
        base_prompt = build_sovereign_prompt(state)
        trauma_text = format_trauma_for_prompt(
            get_trauma(f"stability {state['stability']:.0%}, food {state['food_supply']}", n_results=2)
        )
        decree = context.consume_decree()
        decree_text = (
            f"\n[IMMUTABLE LAW — handed down from beyond]\n{decree}\n"
            f"[This is absolute. Factor it into your decision.]\n"
        ) if decree else ""

        if decree:
            print(f"[TELEGRAM] Decree injected: {decree}")

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": f"{trauma_text}{decree_text}{base_prompt}"}],
        )
        decision = response["message"]["content"].strip()
        return {
            "sovereign_last_decision": decision,
            "log": [f"Year {state['year']}: Sovereign decrees — \"{decision}\""],
        }
    return node


# ── Graph (same structure as ch04, different node instances) ──────────────────

def build_graph(checkpointer, context: SimulationContext):
    def should_continue(state: WorldState) -> str:
        if context.trigger_reset:
            context.trigger_reset = False
            return "collapse"
        return "collapse" if state["stability"] <= 0.05 else "world_engine"

    builder = StateGraph(WorldState)
    builder.add_node("world_engine", world_engine_with_events(context))
    builder.add_node("sovereign", sovereign_with_decree(context))
    builder.add_node("apply_decision", apply_decision_node)
    builder.set_entry_point("world_engine")
    builder.add_edge("world_engine", "sovereign")
    builder.add_edge("sovereign", "apply_decision")
    builder.add_conditional_edges(
        "apply_decision", should_continue,
        {"world_engine": "world_engine", "collapse": END},
    )
    return builder.compile(checkpointer=checkpointer)


# ── Async simulation loop ─────────────────────────────────────────────────────

async def simulation_loop(context: SimulationContext, bot_app, admin_id: int):
    era = 1
    current_input = None

    while True:
        print(f"\n[ERA {era}] Civilization begins...")

        with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
            graph = build_graph(checkpointer, context)
            config = {"configurable": {"thread_id": THREAD_ID}}

            if era == 1 and current_input is None:
                existing = graph.get_state(config)
                current_input = None if existing.values else create_initial_state()
                if existing.values:
                    print(f"[RESUME] Year {existing.values.get('year', '?')}")

            # Run the graph, yielding between ticks so the bot can process commands
            loop = asyncio.get_event_loop()
            states = await loop.run_in_executor(
                None,
                lambda: list(graph.stream(current_input, config=config, stream_mode="values"))
            )
            for state_update in states:
                context.update_from_state(state_update)
                await check_threshold_events(state_update, context, bot_app, admin_id)
                print_tick(state_update)
                await asyncio.sleep(TICK_DELAY)

            final = graph.get_state(config)
            final_state = final.values if final.values else {}

        if final_state.get("stability", 1.0) <= 0.05 or context.trigger_reset:
            await send_notification(
                bot_app, admin_id,
                f"💀 *ERA {era} HAS ENDED* — Year {final_state.get('year', '?')}\n"
                f"_The Great Reset begins._"
            )
            current_input = great_reset(final_state)
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            era += 1
        else:
            break


async def main_async():
    token, admin_id = load_config()
    context = SimulationContext()
    bot_app = build_bot(context, admin_id)

    print("=" * 60)
    print("The Gilded Void — Chapter 05: Telegram Bridge")
    print(f"Send /help to your bot on Telegram. Admin ID: {admin_id}")
    print("=" * 60)

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await send_notification(bot_app, admin_id,
        "🔱 *The Gilded Void is awakening.*\nSend /status to check the world.")

    try:
        await simulation_loop(context, bot_app, admin_id)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[PAUSED] Shutting down...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--wipe-memory", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if args.wipe_memory:
        from chapter_04.memory_store import wipe_memories
        wipe_memories()

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
