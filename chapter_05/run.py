"""
Chapter 05 - Simulation + Telegram Bridge

Runs the simulation and the Telegram bot concurrently using asyncio.

Usage:
  python -m chapter_05.run
  python -m chapter_05.run --reset
  python -m chapter_05.run --reset --wipe-memory
"""

import asyncio
import os
import time
import argparse

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from chapter_02.world_state import WorldState, create_initial_state
from chapter_03.world_engine import apply_decision_node
from chapter_04.great_reset import great_reset
from chapter_04.memory_store import get_trauma, format_trauma_for_prompt
from chapter_04.run import sovereign_node_with_memory
from chapter_05.telegram_bridge import SimulationContext, build_bot, load_config
from chapter_05.threshold_events import check_threshold_events

import ollama


DB_PATH = "simulation.db"
THREAD_ID = "gilded_void_timeline_1"
TICK_DELAY = 3.0  # slightly longer to give async tasks time to process


def world_engine_with_events(context: SimulationContext):
    """
    Returns a world_engine node that also applies any pending Architect events.
    We wrap it in a closure so the node can access the shared context.
    """
    from chapter_03.world_engine import world_engine_node

    def node(state: WorldState) -> dict:
        # First apply normal world events
        updates = world_engine_node(state)

        # Then check for pending Architect interventions
        event = context.consume_event()
        if event == "famine":
            updates["food_supply"] = max(0, state["food_supply"] - 2000)
            updates["stability"] = max(0.0, state.get("stability", 0.5) - 0.15)
            updates["log"] = updates.get("log", []) + [
                f"Year {state['year']}: DIVINE INTERVENTION — The Architect has decreed famine."
            ]
            print("[TELEGRAM] Architect-triggered famine applied.")

        elif event == "prosperity":
            updates["food_supply"] = state["food_supply"] + 3000
            updates["stability"] = min(1.0, state.get("stability", 0.5) + 0.10)
            updates["log"] = updates.get("log", []) + [
                f"Year {state['year']}: DIVINE INTERVENTION — The Architect has granted abundance."
            ]
            print("[TELEGRAM] Architect-triggered prosperity applied.")

        return updates

    return node


def sovereign_with_decree(context: SimulationContext):
    """
    Returns a Sovereign node that injects any pending divine decree.
    """
    from chapter_02.first_agent import build_sovereign_prompt, MODEL

    def node(state: WorldState) -> dict:
        base_prompt = build_sovereign_prompt(state)

        # Inject ancestral memory
        memories = get_trauma(
            f"stability {state['stability']:.0%}, food {state['food_supply']}",
            n_results=2
        )
        trauma_text = format_trauma_for_prompt(memories)

        # Inject divine decree if one is pending
        decree = context.consume_decree()
        decree_text = ""
        if decree:
            decree_text = (
                f"\n[IMMUTABLE LAW — handed down from beyond]\n"
                f"{decree}\n"
                f"[This is absolute. Factor it into your decision.]\n"
            )
            print(f"[TELEGRAM] Divine decree injected: {decree}")

        full_prompt = f"{trauma_text}{decree_text}{base_prompt}"

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": full_prompt}],
        )
        decision = response["message"]["content"].strip()

        return {
            "sovereign_last_decision": decision,
            "log": [f"Year {state['year']}: Sovereign decrees — \"{decision}\""],
        }

    return node


def should_continue(context: SimulationContext):
    """Returns a routing function that also checks for manual reset."""
    def router(state: WorldState) -> str:
        if context.trigger_reset:
            context.trigger_reset = False
            return "collapse"
        if state["stability"] <= 0.05:
            return "collapse"
        return "world_engine"
    return router


def build_graph(checkpointer, context: SimulationContext):
    builder = StateGraph(WorldState)

    builder.add_node("world_engine", world_engine_with_events(context))
    builder.add_node("sovereign", sovereign_with_decree(context))
    builder.add_node("apply_decision", apply_decision_node)

    builder.set_entry_point("world_engine")
    builder.add_edge("world_engine", "sovereign")
    builder.add_edge("sovereign", "apply_decision")

    builder.add_conditional_edges(
        "apply_decision",
        should_continue(context),
        {"world_engine": "world_engine", "collapse": END},
    )

    return builder.compile(checkpointer=checkpointer)


async def simulation_loop(context: SimulationContext, bot_app, admin_id: int):
    """
    The main simulation loop, running as an async task.
    Yields control to the event loop between ticks so the bot can process commands.
    """
    era = 1
    current_input = None

    while True:
        print(f"\n[ERA {era}] Civilization begins...")

        with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
            graph = build_graph(checkpointer, context)
            sim_config = {"configurable": {"thread_id": THREAD_ID}}

            if era == 1 and current_input is None:
                existing = graph.get_state(sim_config)
                if existing.values:
                    print(f"[RESUME] Resuming from Year {existing.values.get('year', '?')}")
                    current_input = None
                else:
                    current_input = create_initial_state()

            # Stream through the graph
            async for state_update in _async_stream(graph, current_input, sim_config):
                # Update shared context so bot can answer /status
                context.update_from_state(state_update)

                # Check threshold events
                await check_threshold_events(state_update, context, bot_app, admin_id)

                # Print tick summary
                _print_tick(state_update)

                # Yield to the event loop so Telegram commands can be processed
                await asyncio.sleep(TICK_DELAY)

            final = graph.get_state(sim_config)
            final_state = final.values if final.values else {}

        if final_state.get("stability", 1.0) <= 0.05 or context.trigger_reset:
            # Civilization collapsed
            from chapter_05.telegram_bridge import send_notification
            await send_notification(
                bot_app, admin_id,
                f"💀 *ERA {era} HAS ENDED*\n\nThe civilization has collapsed in Year {final_state.get('year', '?')}.\n"
                f"The Architect observes the ruins with detached satisfaction.\n\n_The Great Reset begins._"
            )
            current_input = great_reset(final_state)
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            era += 1
        else:
            break


async def _async_stream(graph, input_state, config):
    """
    Wraps LangGraph's synchronous stream() in an async generator.
    This lets us use 'async for' and await between ticks.
    """
    loop = asyncio.get_event_loop()

    def _sync_stream():
        return list(graph.stream(input_state, config=config, stream_mode="values"))

    # Run the synchronous stream in a thread pool to avoid blocking the event loop
    states = await loop.run_in_executor(None, _sync_stream)
    for state in states:
        yield state


def _print_tick(state: dict):
    stability = state.get("stability", 0)
    bar = "█" * int(stability * 20) + "░" * (20 - int(stability * 20))
    print(f"\n{'─' * 60}")
    print(f"  YEAR {state.get('year', '?'):>4}  │  Pop: {state.get('population', 0):>7,}  │  Food: {state.get('food_supply', 0):>7,}")
    print(f"  Stability [{bar}] {stability:.0%}")
    decision = state.get("sovereign_last_decision", "")
    if decision:
        print(f"  Decision: {decision[:55]}")
    for entry in state.get("log", [])[-2:]:
        print(f"  › {entry}")


async def main_async():
    token, admin_id = load_config()

    context = SimulationContext()
    bot_app = build_bot(context, admin_id)

    print("=" * 60)
    print("The Gilded Void — Chapter 05: Telegram Bridge")
    print("=" * 60)
    print(f"Bot is live. Send /help to your bot on Telegram.")
    print(f"Admin ID: {admin_id}")
    print("=" * 60)

    # Initialize the bot
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()

    # Send a startup notification
    from chapter_05.telegram_bridge import send_notification
    await send_notification(
        bot_app, admin_id,
        "🔱 *The Gilded Void is awakening.*\n\nThe simulation is starting. Send /status to check the world."
    )

    try:
        # Run simulation loop (this runs until KeyboardInterrupt)
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
        print("[RESET] Simulation wiped.")
    if args.wipe_memory:
        from chapter_04.memory_store import wipe_memories
        wipe_memories()

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
