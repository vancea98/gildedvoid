"""
Chapter 05 - The Telegram Bridge

Provides the Architect's interface to the simulation.
Runs concurrently with the simulation loop using asyncio.

The bridge does two things:
  1. Receives commands from the Architect and applies them to the simulation
  2. Sends notifications when Threshold Events occur

The simulation state is shared via a thread-safe SimulationContext object
that both the simulation loop and the bot handlers can read/write.
"""

import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


def load_config() -> tuple[str, int]:
    """
    Loads bot token and admin ID from environment or .env file.
    Returns (token, admin_id).
    """
    # Try loading from .env file manually (no extra dependencies needed)
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    token = os.environ.get("TELEGRAM_TOKEN", "")
    admin_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "0")

    if not token:
        raise RuntimeError(
            "TELEGRAM_TOKEN not found.\n"
            "Create a .env file with:\n"
            "  TELEGRAM_TOKEN=your_token_here\n"
            "  TELEGRAM_ADMIN_ID=your_user_id_here\n"
            "Get a token from @BotFather on Telegram."
        )

    return token, int(admin_id_str)


@dataclass
class SimulationContext:
    """
    Shared state between the simulation loop and the Telegram bot.

    The simulation writes current world state here each tick.
    The bot reads from here to answer /status queries.
    The bot writes pending_decree here when the Architect sends a command.
    The simulation reads pending_decree each tick and injects it if present.
    """
    # Current world state (updated each tick by the simulation)
    current_year: int = 0
    current_stability: float = 0.75
    current_population: int = 0
    current_food: int = 0
    current_ideology: str = ""
    current_decision: str = ""

    # Pending divine decree (set by bot, consumed by simulation)
    pending_decree: Optional[str] = None

    # Pending world event (set by bot, consumed by simulation)
    pending_event: Optional[str] = None

    # Flag to trigger Great Reset
    trigger_reset: bool = False

    # Threshold event tracking
    simulation_mentions: int = 0  # for Esoteric Breakthrough detection

    def update_from_state(self, state: dict):
        """Called by the simulation each tick to sync current state."""
        self.current_year = state.get("year", 0)
        self.current_stability = state.get("stability", 0.0)
        self.current_population = state.get("population", 0)
        self.current_food = state.get("food_supply", 0)
        self.current_ideology = state.get("sovereign_ideology", "")[:80]
        self.current_decision = state.get("sovereign_last_decision", "")[:100]

    def consume_decree(self) -> Optional[str]:
        """Returns the pending decree and clears it."""
        decree = self.pending_decree
        self.pending_decree = None
        return decree

    def consume_event(self) -> Optional[str]:
        """Returns the pending event and clears it."""
        event = self.pending_event
        self.pending_event = None
        return event


def build_bot(context: SimulationContext, admin_id: int) -> Application:
    """
    Builds the Telegram bot application with all command handlers.
    """
    token, _ = load_config()
    app = Application.builder().token(token).build()

    def admin_only(handler):
        """Decorator that restricts commands to the admin user."""
        async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id != admin_id:
                await update.message.reply_text("Access denied. The Void does not answer to you.")
                return
            await handler(update, ctx)
        return wrapper

    @admin_only
    async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Returns the current world state."""
        stability_bar = "█" * int(context.current_stability * 10) + "░" * (10 - int(context.current_stability * 10))
        msg = (
            f"📊 *WORLD STATUS — Year {context.current_year}*\n\n"
            f"Population: `{context.current_population:,}`\n"
            f"Food Supply: `{context.current_food:,}`\n"
            f"Stability: `[{stability_bar}] {context.current_stability:.0%}`\n\n"
            f"*Ideology:*\n_{context.current_ideology}_\n\n"
            f"*Last Decision:*\n_{context.current_decision}_"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    @admin_only
    async def cmd_decree(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Injects a divine decree into the next Sovereign prompt."""
        if not ctx.args:
            await update.message.reply_text("Usage: /decree [your decree text]")
            return
        decree = " ".join(ctx.args)
        context.pending_decree = decree
        await update.message.reply_text(
            f"⚡ *Divine Decree received.*\n\n_{decree}_\n\n"
            f"It will be injected into the Sovereign's next thought.",
            parse_mode="Markdown"
        )

    @admin_only
    async def cmd_famine(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Triggers an immediate famine."""
        context.pending_event = "famine"
        await update.message.reply_text("🌵 *Famine decreed.* The granaries will be found empty.", parse_mode="Markdown")

    @admin_only
    async def cmd_prosperity(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Grants a food surplus."""
        context.pending_event = "prosperity"
        await update.message.reply_text("🌾 *Prosperity granted.* The harvests overflow.", parse_mode="Markdown")

    @admin_only
    async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Manually triggers the Great Reset."""
        context.trigger_reset = True
        await update.message.reply_text(
            "💀 *The Great Reset approaches.* The civilization will be judged.",
            parse_mode="Markdown"
        )

    @admin_only
    async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        msg = (
            "🔱 *Architect Commands*\n\n"
            "/status — Current world stats\n"
            "/decree [text] — Inject a divine decree\n"
            "/famine — Trigger immediate famine\n"
            "/prosperity — Grant a food surplus\n"
            "/reset — Manually trigger the Great Reset\n"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("decree", cmd_decree))
    app.add_handler(CommandHandler("famine", cmd_famine))
    app.add_handler(CommandHandler("prosperity", cmd_prosperity))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))

    return app


async def send_notification(app: Application, admin_id: int, message: str):
    """Sends a notification message to the Architect."""
    try:
        await app.bot.send_message(chat_id=admin_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"[TELEGRAM] Failed to send notification: {e}")
