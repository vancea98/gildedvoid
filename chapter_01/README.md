# Chapter 01 — Environment Setup

Before writing a single line of simulation code, we need a clean, isolated workspace.
This chapter explains *why* each step matters, not just *what* to type.

---

## Concept: Virtual Environments

Imagine you're building two separate projects:
- Project A needs version 1.0 of a library
- Project B needs version 2.0 of the same library

If you install everything globally, they conflict. A **virtual environment** is a
self-contained Python installation just for one project. Dependencies live inside it
and don't interfere with anything else on your machine.

Think of it as a clean room for each project.

---

## Step 1 — Create the Virtual Environment

Open a terminal in `C:\Users\mihai\piedpapers\` and run:

```bash
python -m venv .venv
```

This creates a hidden folder called `.venv` containing a fresh Python installation.
You'll never edit files inside `.venv` directly — Python manages it for you.

---

## Step 2 — Activate It

Every time you open a new terminal to work on this project, you must activate the environment:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

You'll know it's active when you see `(.venv)` at the start of your terminal prompt.

> If PowerShell blocks the script with an execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> Then try activating again.

---

## Step 3 — Install Our Dependencies

With the environment active, install the libraries we'll use throughout the guide:

```bash
pip install langgraph langgraph-checkpoint-sqlite langchain-core chromadb python-telegram-bot ollama
```

What each one does:
- `langgraph` — the framework that manages our simulation loop
- `langchain-core` — base types that LangGraph builds on
- `chromadb` — the local vector database for ancestral memory
- `python-telegram-bot` — lets us send/receive Telegram messages from Python
- `ollama` — the Python client that talks to our local AI models

This will take a minute. You'll see a lot of output — that's normal.

---

## Step 4 — Install Ollama (The AI Model Runner)

Ollama is a separate application (not a Python library) that runs AI models on your GPU.

Since you already have **Scoop** installed (it manages your Python too), use it:

```powershell
scoop install ollama
```

Scoop installs Ollama and adds it to your PATH automatically — no manual steps needed.

> **No Scoop?** Download the Windows installer from ollama.com, run it,
> then close and reopen PowerShell before continuing (so PATH updates take effect).

After installing, pull the model we'll use:

```powershell
ollama pull gemma3:4b
```

This downloads a 4-billion parameter version of Google's Gemma 3 model (~2.5GB).
It's small enough to run fast on your 3060 Ti while being smart enough to reason well.

To verify it works, run a quick test:
```powershell
ollama run gemma3:4b "Say hello in one sentence."
```

You should see the model respond. If it does, you're ready.

---
If Ollama is installed but Windows can't find it, you can use Scoop (it manages Python too) — you just downloaded the bucket manifest. Install it properly through Scoop:

```powershell
scoop install ollama
```

That's it. Scoop will install Ollama and add it to your PATH automatically. After it finishes, run:

```powershell
ollama pull gemma3:4b
```
If scoop install ollama fails for any reason, you can also install Ollama manually — download the Windows installer from ollama.com, run it, then close and reopen PowerShell before trying ollama pull again (the new terminal will have the updated PATH).
## Step 5 — Verify Everything Works

Run the verification script:

```powershell
python -m chapter_01.verify
```

Expected output:
```
[OK] Python version: 3.13.x
[OK] LangGraph imported
[OK] ChromaDB imported
[OK] Ollama client imported
[OK] Ollama is running and gemma3:4b is available
All checks passed. You're ready for Chapter 02.
```

---

## Concept: What is a Language Model, Actually?

Before we go further, it helps to have a mental model of what these AI models actually do.

A language model takes text as input and predicts the most likely next token (roughly: next
word). That's it. It does this billions of times, producing a coherent response.

What makes it useful for simulation:
- You can give it a *role* ("You are the leader of a civilization in year 347...")
- You can give it *context* ("Your population is starving. Resources are at 12%...")
- It will *reason* within that context and produce a decision

It's not thinking. It's a very sophisticated pattern-completion engine.
But for our purposes — simulating how a leader *would* reason under pressure —
it's remarkably effective.

---

## Concept: What is LangGraph?

LangGraph lets you build **stateful graphs** where nodes are functions and edges are
the flow between them.

In our simulation:
```
[Tick Start] → [Observe] → [Think] → [Act] → [Tick Start] → ...
```

Each arrow is an edge. Each box is a node. The loop runs forever until you stop it.
LangGraph also handles saving the state between steps — so if your PC crashes,
the simulation resumes exactly where it left off.

We'll see this in action starting in Chapter 02.

---

## Your Project Structure So Far

```
piedpapers/
├── .venv/              ← your virtual environment (never edit manually)
├── README.md           ← the guide index
└── chapter_01/
    ├── README.md       ← this file
    └── verify.py       ← the verification script
```

---

Next: [Chapter 02 — Your First Agent](../chapter_02/README.md)
