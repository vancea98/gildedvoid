# Chapter 02 — Your First Agent

In this chapter we build the simplest possible LangGraph agent and run it.
By the end, you'll have an AI that can hold a "world state" and reason about it.

---

## Concept: State

Every simulation needs to track "what is currently true about the world."
In LangGraph, this is called **state** — a Python dictionary that every node can read and write.

For our simulation, the world state might look like:

```python
{
    "year": 347,
    "population": 12000,
    "food_supply": 800,
    "stability": 0.72,
    "log": ["Year 347: Drought begins in the eastern provinces."]
}
```

Every tick of the simulation, a node reads this state, thinks about it, and returns
an updated version. LangGraph merges the updates automatically.

---

## Concept: Nodes and Edges

A **node** is just a Python function that:
1. Receives the current state
2. Does something (calls an AI model, runs a calculation, etc.)
3. Returns a dictionary of state updates

An **edge** connects one node to the next, defining the flow of execution.

```
node_a  -->  node_b  -->  node_c
```

When node_a finishes, LangGraph automatically calls node_b with the updated state.

---

## Concept: The TypedDict

Python's `TypedDict` lets us define exactly what fields our state has,
with type hints. This helps catch bugs early and makes the code readable.

```python
from typing import TypedDict, Annotated
import operator

class WorldState(TypedDict):
    year: int
    stability: float
    log: Annotated[list[str], operator.add]  # explained below
```

The `Annotated[list[str], operator.add]` part tells LangGraph:
"when merging state updates, add lists together instead of replacing them."
This means every node can append to the log without overwriting what previous nodes wrote.

---

## The Files

- `world_state.py` — defines our shared state structure
- `first_agent.py` — a single agent that observes the world and thinks about it
- `run.py` — runs the agent once and prints the result

Work through them in order. Read every comment.

---

## Running It

```powershell
python -m chapter_02.run
```

You should see the agent receive a world state and produce a response.
The response won't do anything yet — that's Chapter 03.

---

## Key Insight

Notice that the agent doesn't "know" it's in a simulation.
It just receives text describing a world and responds to it.
This is the foundation of everything else we'll build:
the agent's "reality" is entirely defined by what we put in its prompt.

---

Next: [Chapter 03 — The Infinite Loop](../chapter_03/README.md)
