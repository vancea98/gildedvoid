# The Gilded Void — A Builder's Guide

> You are the Architect. Civilizations rise, radicalize, and collapse chasing a hollow throne.
> This guide builds that simulation from zero — one concept at a time.

---

## What We're Building

A persistent, always-on multi-agent simulation running entirely on your local machine.
Multiple AI agents play the roles of civilizations. You play the devil watching from above,
intervening through your phone via Telegram.

The deeper point: by building it, you'll learn how real AI agent systems work.

---

## The Stack

| Tool | What it does |
|---|---|
| **Python** | The language everything runs in |
| **LangGraph** | Manages the simulation loop and agent state |
| **Ollama** | Runs AI models locally on your GPU |
| **ChromaDB** | Stores memories that survive across resets |
| **python-telegram-bot** | Your "divine interface" — control from anywhere |

---

## The Road Map

Each chapter builds on the last. Don't skip ahead.

| Chapter | Title | What you learn |
|---|---|---|
| [01](./chapter_01/README.md) | Environment Setup | Virtual envs, pip, project structure |
| [02](./chapter_02/README.md) | Your First Agent | LangGraph basics, nodes, state |
| [03](./chapter_03/README.md) | The Infinite Loop + Persistence | Cyclic graphs, the simulation tick, Checkpointers and persistence |
| [05](./chapter_04/README.md) | Ancestral Memory | ChromaDB, vector search, trauma vectors |
| [06](./chapter_05/README.md) | The Telegram Bridge | Async bots, divine decrees, HITL |
| [07](./chapter_06/README.md) | The Gilded Void v0.1 | Bringing it all together |

---

## Before You Start

You need:
- Python 3.10 or higher (you have 3.13 — good)
- A GPU (your RTX 3060 Ti is perfect)
- Ollama installed (we cover this in Chapter 01)
- About 10GB of free disk space for models

---

## How to Use This Guide

Each chapter has:
- A `README.md` explaining the concepts in plain English
- Python files you actually run
- Comments in the code explaining every line

Read the README first. Then run the code. Then modify it.
Breaking things is part of learning.

---

*"The Architect does not want the civilization to win; the Architect wants them to bleed in interesting patterns."*
