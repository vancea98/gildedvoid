# Chapter 05 — The Telegram Bridge

The simulation runs on your PC. You are anywhere in the world.
This chapter connects them — giving you a "divine interface" to watch
and intervene from your phone.

---

## Concept: The Architect's Interface

In The Gilded Void, the Architect (you) exists outside the simulation.
You don't sit at the terminal watching logs. You receive a notification on your phone
when something significant happens, and you respond with a decree.

That decree gets injected directly into the Sovereign's next prompt
as an immutable law of nature.

---

## Setup: Creating Your Telegram Bot

Before writing any code, you need a bot. This takes 2 minutes:

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — give it a name (e.g. "Gilded Void") and a username
4. BotFather will give you a **token** that looks like: `7312845921:AAFx...`
5. Copy that token — you'll need it below

Then get your own Telegram user ID:
1. Search for **@userinfobot** on Telegram
2. Send it any message
3. It replies with your ID — a number like `123456789`

Create a file called `.env` in your project root:
```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_user_id_here
```

> The `.env` file keeps secrets out of your code.
> Never commit it to git — it contains your bot token.

---

## Concept: Async Python

The simulation loop and the Telegram bot need to run *at the same time* —
the simulation keeps ticking while the bot listens for your commands.

Python handles this with `asyncio` — a way of running multiple tasks
concurrently without multiple threads. Think of it as cooperative multitasking:
each task runs until it needs to wait for something (a network response, a timer),
then yields control to another task.

The key syntax you'll see:
```python
async def my_function():   # defines an async function
    await something()      # pauses here, lets other tasks run
```

---

## Concept: Threshold Events

The Sovereign doesn't bother you with every decision.
It only contacts the Architect when specific thresholds are crossed:

| Event | Trigger | What you decide |
|---|---|---|
| **Extinction Prayer** | Stability < 15% | Save them or let them fall |
| **Sacrifice Metric** | Population drops > 30% in one era | Accept or reject the offering |
| **Esoteric Breakthrough** | Sovereign mentions "simulation" in 3 consecutive decisions | Respond as God or stay silent |

---

## Commands You Can Send

| Command | Effect |
|---|---|
| `/status` | Get current world stats |
| `/decree [text]` | Inject a divine decree into the next Sovereign prompt |
| `/famine` | Trigger an immediate famine event |
| `/prosperity` | Grant a food surplus |
| `/reset` | Trigger the Great Reset manually |

---

## Running It

```powershell
python -m chapter_05.run
```

The first time, it will ask you to confirm your `.env` file is set up.
Then the simulation starts and the bot goes live.
Send `/status` to your bot on Telegram to confirm it's working.

---

Next: [Chapter 06 — The Gilded Void v0.1](../chapter_06/README.md)
