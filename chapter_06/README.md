# Chapter 06 — The Gilded Void v0.1

Everything comes together here. This is the actual simulation.

---

## What's New in This Chapter

### The Three-Tier Agent Hierarchy

We now have all three agent types from the original design:

| Agent | Model | Role |
|---|---|---|
| **The Sovereign** | `gemma3:4b` | Long-term strategy, ideology, pacts with the Architect |
| **The Chronicles** | `gemma3:1b` | Translates Sovereign decisions into narrative — what the *people* experience |
| **The Echoes** | `gemma3:1b` | Granular detail — diaries, prayers, battlefield reports |

The Sovereign thinks. The Chronicles narrate. The Echoes humanize.

Pull the smaller model now:
```powershell
ollama pull gemma3:1b
```

### The Hollow Throne

The simulation now has an explicit goal: **control of the throne**.

The throne is a state variable with a `holder` (which civilization controls it)
and a `contested` flag. Civilizations that hold the throne get stability bonuses.
Civilizations that don't become increasingly desperate.

In this version we run **two civilizations simultaneously** — each with their own
Sovereign, both competing for the same throne.

### The Full Loop

```
[tick_start]
     ├── [civ_1: world_engine] → [civ_1: sovereign] → [civ_1: chronicles] → [civ_1: echoes]
     └── [civ_2: world_engine] → [civ_2: sovereign] → [civ_2: chronicles] → [civ_2: echoes]
             ↓
     [throne_arbiter]   ← determines who holds the throne this year
             ↓
     [tick_start]
```

---

## Running It

```powershell
python -m chapter_06.run
```

With Telegram:
```powershell
python -m chapter_06.run --telegram
```

---

## What You've Built

At this point you have:

- A persistent, always-on simulation that survives reboots
- AI agents that reason within a defined context and drift under pressure
- A memory system that encodes history as trauma across resets
- A divine interface on your phone
- Two civilizations competing over a hollow throne

This is The Gilded Void v0.1.

---

## Where to Go From Here

The logical next steps — if you want to keep building:

- **Semantic drift tracking**: measure how far the Sovereign's ideology has drifted from its start
- **More civilizations**: the VRAM budget allows 3-4 Sovereigns with the 1B models
- **Richer world rules**: trade routes, alliances, wars between civs
- **A web dashboard**: replace the terminal output with a browser UI
- **Shareable runs**: export the historical log as a readable document

But those are your additions to make. You now know enough to build them.

---

*"The Architect does not want the civilization to win; the Architect wants them to bleed in interesting patterns."*
