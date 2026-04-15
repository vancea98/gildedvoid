"""
Chapter 06 - The Gilded Void v0.1

The capstone. Everything from previous chapters plus:
  - Two civilizations running simultaneously
  - The Hollow Throne (a contested goal both civs fight over)
  - Three-tier agents: Sovereign (4b), Chronicles (1b), Echoes (1b)
  - Optional Telegram interface

This file is self-contained — it doesn't import run logic from previous chapters,
only their reusable components (nodes, memory, agents). That way you can read
this file alone and understand the complete simulation.

Usage:
  python -m chapter_06.run                    ← terminal only
  python -m chapter_06.run --telegram         ← with Telegram
  python -m chapter_06.run --reset            ← start fresh
  python -m chapter_06.run --reset --wipe-memory
"""

import asyncio
import argparse
import time
import os

from chapter_02.world_state import create_initial_state
from chapter_04.memory_store import wipe_memories
from chapter_06.gilded_void import CIV_NAMES, HollowThrone, run_tick, collapse_civilization

TICK_DELAY = 2.5


# ── Display ───────────────────────────────────────────────────────────────────

def print_world(civ_states: dict, throne: HollowThrone, tick: int):
    print(f"\n{'═' * 64}")
    print(f"  YEAR {tick:<6} │  {throne.status()}")
    print(f"{'═' * 64}")
    for name in CIV_NAMES:
        s = civ_states[name]
        stab = s.get("stability", 0)
        bar = "█" * int(stab * 15) + "░" * (15 - int(stab * 15))
        crown = " 👑" if throne.holder == name else ""
        print(f"\n  {name}{crown}")
        print(f"  Pop: {s.get('population', 0):>7,}  │  Food: {s.get('food_supply', 0):>7,}  │  [{bar}] {stab:.0%}")
        decision = s.get("sovereign_last_decision", "")
        if decision:
            print(f"  ↳ {decision[:70]}")
        for entry in s.get("log", [])[-3:]:
            print(f"    {entry}")


# ── Fresh state for a named civilization ──────────────────────────────────────

def new_civ_state(name: str, era: int, trauma_ideology: str = "") -> dict:
    state = create_initial_state()
    if trauma_ideology:
        state["sovereign_ideology"] = trauma_ideology
        state["log"] = [f"Era {era}, Year 1: {name} is reborn. Something inherited from the past stirs uneasily."]
    else:
        state["log"] = [f"Era {era}, Year 1: {name} awakens. The hollow throne stands empty."]
    return state


# ── Terminal mode ─────────────────────────────────────────────────────────────

def run_terminal(reset: bool, wipe_mem: bool):
    if wipe_mem:
        wipe_memories()

    print("=" * 64)
    print("  THE GILDED VOID v0.1")
    print("  Two civilizations. One hollow throne. The Architect watches.")
    print("=" * 64)
    print("  Press Ctrl+C to pause.\n")

    throne = HollowThrone()
    era = 1
    civ_states = {name: new_civ_state(name, era) for name in CIV_NAMES}
    decrees = {name: None for name in CIV_NAMES}

    try:
        tick = 1
        while True:
            # Handle collapses before the next tick
            for name in CIV_NAMES:
                if civ_states[name].get("stability", 1.0) <= 0.05:
                    new_state = collapse_civilization(name, civ_states[name], era)
                    civ_states[name] = new_state
                    era += 1

            civ_states = run_tick(civ_states, throne, decrees, era)
            print_world(civ_states, throne, tick)
            tick += 1
            time.sleep(TICK_DELAY)

    except KeyboardInterrupt:
        print("\n\n[PAUSED] The Architect steps away. The world holds its breath.")


# ── Telegram mode ─────────────────────────────────────────────────────────────

async def run_telegram(reset: bool, wipe_mem: bool):
    from chapter_05.telegram_bridge import SimulationContext, build_bot, load_config, send_notification
    from chapter_05.threshold_events import check_threshold_events

    if wipe_mem:
        wipe_memories()

    _, admin_id = load_config()
    context = SimulationContext()
    bot_app = build_bot(context, admin_id)

    print("=" * 64)
    print("  THE GILDED VOID v0.1 — with Telegram")
    print(f"  Admin ID: {admin_id}  |  Send /help to your bot.")
    print("=" * 64)

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await send_notification(bot_app, admin_id,
        "🔱 *The Gilded Void awakens.*\n"
        "Two civilizations — *Valdris* and *Sorreth* — compete for the hollow throne.\n"
        "Send /help for commands."
    )

    throne = HollowThrone()
    era = 1
    civ_states = {name: new_civ_state(name, era) for name in CIV_NAMES}

    try:
        tick = 1
        while True:
            # Handle collapses
            for name in CIV_NAMES:
                if civ_states[name].get("stability", 1.0) <= 0.05:
                    await send_notification(bot_app, admin_id,
                        f"💀 *{name} HAS FALLEN* — Year {civ_states[name].get('year', '?')}\n"
                        f"The Great Reset claims another civilization."
                    )
                    new_state = collapse_civilization(name, civ_states[name], era)
                    civ_states[name] = new_state
                    era += 1

            # Route Architect commands: decree goes to weakest civ, events affect all
            weakest = min(CIV_NAMES, key=lambda n: civ_states[n].get("stability", 1.0))
            pending_decree = context.consume_decree()
            decrees = {name: (pending_decree if name == weakest else None) for name in CIV_NAMES}

            event = context.consume_event()
            if event == "famine":
                civ_states[weakest]["food_supply"] = max(0, civ_states[weakest]["food_supply"] - 2000)
                civ_states[weakest]["stability"] = max(0.0, civ_states[weakest]["stability"] - 0.15)
            elif event == "prosperity":
                civ_states[weakest]["food_supply"] += 3000
                civ_states[weakest]["stability"] = min(1.0, civ_states[weakest]["stability"] + 0.10)

            # Manual reset
            if context.trigger_reset:
                context.trigger_reset = False
                name_to_reset = weakest
                await send_notification(bot_app, admin_id,
                    f"⚡ *The Architect has ended {name_to_reset}.*")
                new_state = collapse_civilization(civ_states[name_to_reset], civ_states[name_to_reset], era)
                civ_states[name_to_reset] = new_state
                era += 1

            civ_states = run_tick(civ_states, throne, decrees, era)

            # Check threshold events for each civilization
            for name in CIV_NAMES:
                await check_threshold_events(civ_states[name], context, bot_app, admin_id)

            # Update bot context with combined world status
            context.update_from_state({
                **civ_states[CIV_NAMES[0]],
                "year": tick,
                "sovereign_ideology": " | ".join(
                    f"{n}: {civ_states[n].get('sovereign_ideology', '')[:30]}"
                    for n in CIV_NAMES
                ),
            })

            print_world(civ_states, throne, tick)
            tick += 1
            await asyncio.sleep(TICK_DELAY)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[PAUSED] Shutting down...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="The Gilded Void v0.1")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--wipe-memory", action="store_true")
    args = parser.parse_args()

    if args.telegram:
        asyncio.run(run_telegram(args.reset, args.wipe_memory))
    else:
        run_terminal(args.reset, args.wipe_memory)


if __name__ == "__main__":
    main()
