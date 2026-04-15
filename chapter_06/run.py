"""
Chapter 06 - The Gilded Void v0.1 — Main Entry Point

Usage:
  python -m chapter_06.run                 ← run without Telegram
  python -m chapter_06.run --telegram      ← run with Telegram interface
  python -m chapter_06.run --reset         ← start fresh (keeps ancestral memory)
  python -m chapter_06.run --wipe-memory   ← also wipe ancestral memory
"""

import asyncio
import argparse
import time
import os

from chapter_02.world_state import create_initial_state
from chapter_06.gilded_void import (
    CIV_NAMES,
    HollowThrone,
    run_tick,
    collapse_civilization,
)


TICK_DELAY = 2.5
SAVE_FILE = "gilded_void_state.json"  # simple JSON save for the dual-civ setup


def print_world(civ_states: dict, throne, tick: int):
    """Prints a readable tick summary for both civilizations."""
    print(f"\n{'═' * 60}")
    print(f"  YEAR {tick}  │  {throne.status()}")
    print(f"{'═' * 60}")

    for name in CIV_NAMES:
        s = civ_states[name]
        stab = s.get("stability", 0)
        bar = "█" * int(stab * 15) + "░" * (15 - int(stab * 15))
        throne_marker = " 👑" if throne.holder == name else ""
        print(f"\n  {name}{throne_marker}")
        print(f"  Pop: {s.get('population', 0):>7,}  │  Food: {s.get('food_supply', 0):>7,}  │  [{bar}] {stab:.0%}")
        decision = s.get("sovereign_last_decision", "")
        if decision:
            print(f"  ↳ {decision[:70]}")
        for entry in s.get("log", [])[-3:]:
            print(f"    {entry}")


def run_without_telegram(reset: bool, wipe_memory: bool):
    """Runs the simulation in simple terminal mode."""

    if wipe_memory:
        from chapter_04.memory_store import wipe_memories
        wipe_memories()

    print("=" * 60)
    print("  THE GILDED VOID v0.1")
    print("  Two civilizations. One throne. The Architect watches.")
    print("=" * 60)
    print("Press Ctrl+C to pause.\n")

    throne = HollowThrone()
    era = 1

    # Initialize both civilizations
    civ_states = {}
    for name in CIV_NAMES:
        state = create_initial_state()
        state["log"] = [f"Year 1: {name} awakens. The throne stands empty."]
        civ_states[name] = state

    try:
        tick = 1
        while True:
            # Check for collapses
            for name in CIV_NAMES:
                if civ_states[name].get("stability", 1.0) <= 0.05:
                    new_state = collapse_civilization(name, civ_states[name], era)
                    new_state["log"] = [
                        f"Year 1: {name} is reborn from the ashes. Something feels wrong."
                    ]
                    civ_states[name] = new_state
                    era += 1

            # Run one tick (no decrees in terminal mode — use Telegram for that)
            decrees = {name: None for name in CIV_NAMES}
            civ_states = run_tick(civ_states, throne, decrees, era)

            print_world(civ_states, throne, tick)
            tick += 1
            time.sleep(TICK_DELAY)

    except KeyboardInterrupt:
        print("\n\n[PAUSED] The Architect steps away. The world holds its breath.")


async def run_with_telegram(reset: bool, wipe_memory: bool):
    """Runs the simulation with the Telegram interface active."""
    from chapter_05.telegram_bridge import SimulationContext, build_bot, load_config, send_notification

    if wipe_memory:
        from chapter_04.memory_store import wipe_memories
        wipe_memories()

    token, admin_id = load_config()
    context = SimulationContext()
    bot_app = build_bot(context, admin_id)

    print("=" * 60)
    print("  THE GILDED VOID v0.1 (with Telegram)")
    print("=" * 60)

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()

    await send_notification(
        bot_app, admin_id,
        "🔱 *The Gilded Void awakens.*\n\nTwo civilizations compete for the hollow throne.\nSend /help for commands."
    )

    throne = HollowThrone()
    era = 1
    civ_states = {}
    for name in CIV_NAMES:
        state = create_initial_state()
        state["log"] = [f"Year 1: {name} awakens."]
        civ_states[name] = state

    try:
        tick = 1
        while True:
            # Check for collapses
            for name in CIV_NAMES:
                if civ_states[name].get("stability", 1.0) <= 0.05:
                    await send_notification(
                        bot_app, admin_id,
                        f"💀 *{name} HAS FALLEN* — Year {civ_states[name].get('year', '?')}\n"
                        f"The Great Reset claims another civilization."
                    )
                    new_state = collapse_civilization(name, civ_states[name], era)
                    new_state["log"] = [f"Year 1: {name} is reborn from the ashes."]
                    civ_states[name] = new_state
                    era += 1

            # Check for Architect decrees (applies to whichever civ is weakest)
            weakest = min(CIV_NAMES, key=lambda n: civ_states[n].get("stability", 1.0))
            pending = context.consume_decree()
            decrees = {name: (pending if name == weakest else None) for name in CIV_NAMES}

            # Apply pending events to the weakest civ
            event = context.consume_event()
            if event == "famine":
                civ_states[weakest]["food_supply"] = max(0, civ_states[weakest]["food_supply"] - 2000)
            elif event == "prosperity":
                civ_states[weakest]["food_supply"] += 3000

            # Tick
            civ_states = run_tick(civ_states, throne, decrees, era)

            # Update context for /status command
            # Combine both civs into one summary for the bot
            combined = civ_states[CIV_NAMES[0]]
            context.update_from_state({**combined, "year": tick})

            print_world(civ_states, throne, tick)
            tick += 1
            await asyncio.sleep(TICK_DELAY)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[PAUSED] Shutting down...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


def main():
    parser = argparse.ArgumentParser(description="The Gilded Void v0.1")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram interface")
    parser.add_argument("--reset", action="store_true", help="Start fresh")
    parser.add_argument("--wipe-memory", action="store_true", help="Also wipe ancestral memory")
    args = parser.parse_args()

    if args.telegram:
        asyncio.run(run_with_telegram(args.reset, args.wipe_memory))
    else:
        run_without_telegram(args.reset, args.wipe_memory)


if __name__ == "__main__":
    main()
