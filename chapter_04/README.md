# Chapter 04 — Ancestral Memory

This chapter adds the feature that makes The Gilded Void genuinely interesting:
when a civilization dies, its history doesn't disappear. It becomes a *trauma* that
haunts the next civilization — invisibly shaping their behavior from the start.

---

## Concept: Vector Embeddings

Computers can't compare meaning directly. If you ask "is 'famine' related to 'starvation'?",
a regular program would say no — they're different strings. 

An **embedding model** converts text into a list of numbers (a vector) that encodes meaning.
Words with similar meanings end up with similar vectors. So "famine" and "starvation" end
up close together in vector space, even though the strings are different.

```
"famine"      → [0.21, -0.87, 0.44, ...]   ← 384 numbers
"starvation"  → [0.19, -0.91, 0.41, ...]   ← close!
"architecture" → [0.73,  0.12, -0.33, ...]  ← far away
```

This is what makes semantic search possible: instead of matching exact words,
you match *meaning*.

---

## Concept: ChromaDB

ChromaDB is a local vector database. It stores text alongside its embedding vector,
and lets you query "find me the 5 stored memories most similar to this new text."

It runs entirely on your machine — no cloud, no API key.

In our simulation, ChromaDB is the **ancestral memory** — a permanent record that
survives even when the simulation resets.

---

## The Great Reset

When a civilization's stability hits zero, it collapses. Before the simulation resets:

1. The World Engine calls `great_reset()` 
2. We summarize the civilization's full history into a few key "trauma vectors"
3. Those get stored in ChromaDB with metadata: year of collapse, cause of death, ideology at death
4. A new simulation starts fresh — but when the new Sovereign is initialized, we query ChromaDB
   for relevant ancestral memories and inject them as "inherited dread" into the system prompt

The new civilization doesn't *know* about the past. But they *feel* it.

---

## What Changes in the Code

We add two new components:

**`memory_store.py`** — a wrapper around ChromaDB that handles:
- Storing civilization summaries after collapse
- Querying for relevant ancestral memories

**`great_reset.py`** — handles the collapse event:
- Summarizes the civilization's history using the AI
- Stores the summary in ChromaDB
- Resets the world state with ancestral trauma injected

We also update `first_agent.py`'s prompt to include ancestral memories when they exist.

---

## Running It

```powershell
python -m chapter_04.run
```

Use `--reset` to wipe both the simulation state AND the ancestral memory:
```powershell
python -m chapter_04.run --reset
```

Let it run until the first civilization collapses, then watch what changes
in the second civilization's Sovereign behavior.

---

## What to Watch

After the Great Reset, look at the Sovereign's first few decisions in the new era.
They should feel subtly different — more defensive, more paranoid — even though
the new civilization starts with the same numbers as the first one did.

That difference is the ancestral trauma working.

---

Next: [Chapter 05 — The Telegram Bridge](../chapter_05/README.md)
