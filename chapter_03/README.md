# Chapter 03 — The Infinite Loop + Persistence

Chapter 02 ran the Sovereign once and stopped.
Now we make it run forever — and survive if your PC crashes or you close the terminal.

---

## Concept: The Simulation Tick

A "tick" is one full cycle of the simulation:

```
[Start Tick] → [World Events] → [Sovereign Thinks] → [World Updates] → [Start Tick] → ...
```

Each tick represents one year in the simulation.
After every tick, the year increments and the world changes based on the Sovereign's decisions.

We model this as a cyclic graph — instead of ending at `END`, the last node
points back to the first node, creating a loop.

---

## Concept: Checkpointing (How Simulations Survive Reboots)

Every tick, LangGraph saves a **checkpoint** — a complete snapshot of the world state
to an SQLite database file on your disk.

If your PC crashes at tick 10,000, when you restart:
1. LangGraph finds the last checkpoint (tick 9,999)
2. Restores the exact world state from that point
3. Continues as if nothing happened

This is the same mechanism real distributed systems use for fault tolerance.
The database file is just `simulation.db` in your project folder.

---

## Concept: The World Engine

We're introducing a second node: the **World Engine**.

The Sovereign *decides* things. The World Engine *applies consequences*.

If the Sovereign says "we will expand agriculture," the World Engine:
- Increases food supply
- Slightly decreases stability (construction disrupts daily life)
- Adds a log entry

This separation is important:
- The Sovereign is the AI reasoning about what to do
- The World Engine is deterministic logic applying rules

This mirrors the real world: leaders decide, but physics and economics
apply consequences regardless of intent.

---

## New Graph Structure

```
[tick_start]
     ↓
[world_engine]   ← applies environmental events, resource changes
     ↓
[sovereign]      ← AI reasons about the situation, makes a decision
     ↓
[apply_decision] ← translates the decision into state changes
     ↓
[tick_start]     ← loops back (with year + 1)
```

---

## Running It

```powershell
python -m chapter_03.run
```

The simulation will run continuously. Press `Ctrl+C` to stop it.
When you run it again, it will resume from where it left off.

To start fresh (wipe the save):
```powershell
python -m chapter_03.run --reset
```

---

## What to Watch

As you let it run, watch the ideology field in the logs.
Under pressure (low food, low stability), the Sovereign's decisions
will start to sound different. This is Semantic Drift beginning.

You're not programming that behavior — the AI is inferring it from context.

---

Next: [Chapter 04 — Ancestral Memory](../chapter_04/README.md)
