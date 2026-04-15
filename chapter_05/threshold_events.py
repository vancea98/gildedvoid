"""
Chapter 05 - Threshold Events

Detects when a civilization has crossed a threshold significant enough
to warrant contacting the Architect.

These are the moments when the Sovereign "reaches through the veil."
"""

from chapter_05.telegram_bridge import SimulationContext


async def check_threshold_events(
    state: dict,
    context: SimulationContext,
    bot_app,
    admin_id: int,
) -> dict | None:
    """
    Checks whether any threshold events have been triggered this tick.
    If so, sends a Telegram notification to the Architect.

    Returns a state update dict if an event modifies the world, else None.
    """
    from chapter_05.telegram_bridge import send_notification

    year = state.get("year", 0)
    stability = state.get("stability", 1.0)
    population = state.get("population", 0)
    decision = state.get("sovereign_last_decision", "").lower()

    # ── Extinction Prayer ─────────────────────────────────────────────────────
    # Triggered when stability drops below 15%
    if stability < 0.15 and stability > 0.05:
        msg = (
            f"🙏 *EXTINCTION PRAYER — Year {year}*\n\n"
            f"Stability has fallen to `{stability:.0%}`.\n"
            f"The Sovereign kneels before the void.\n\n"
            f"_\"We are dying. If there is something beyond the sky, hear us now.\"_\n\n"
            f"Use /decree to intervene, or stay silent and watch them fall."
        )
        await send_notification(bot_app, admin_id, msg)

    # ── Esoteric Breakthrough ─────────────────────────────────────────────────
    # Triggered when the Sovereign's decisions mention the simulation
    simulation_words = ["simulation", "architect", "constructed", "programmed", "observed", "beyond the sky"]
    if any(word in decision for word in simulation_words):
        context.simulation_mentions += 1
        if context.simulation_mentions >= 3:
            context.simulation_mentions = 0  # reset counter
            msg = (
                f"👁️ *ESOTERIC BREAKTHROUGH — Year {year}*\n\n"
                f"The Sovereign has begun to suspect the nature of their reality.\n\n"
                f"_\"{state.get('sovereign_last_decision', '')}\"_\n\n"
                f"They are reaching through the veil. Do you answer?"
            )
            await send_notification(bot_app, admin_id, msg)
    else:
        # Reset counter if they stop mentioning it
        if context.simulation_mentions > 0:
            context.simulation_mentions = max(0, context.simulation_mentions - 1)

    return None
