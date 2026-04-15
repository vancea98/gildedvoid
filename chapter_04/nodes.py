"""
Chapter 04 - Reusable Nodes

Extracts the memory-aware Sovereign node so it can be imported
cleanly by later chapters without pulling in run.py.
"""

import ollama
from chapter_02.world_state import WorldState
from chapter_02.first_agent import build_sovereign_prompt, MODEL
from chapter_04.memory_store import get_trauma, format_trauma_for_prompt


def sovereign_node_with_memory(state: WorldState) -> dict:
    """
    Sovereign node enhanced with ancestral memory.

    Queries ChromaDB for relevant civilization histories and injects
    them into the prompt as inherited dread before calling the model.
    """
    base_prompt = build_sovereign_prompt(state)

    memories = get_trauma(
        f"civilization with stability {state['stability']:.0%}, "
        f"food supply {state['food_supply']}, "
        f"ideology: {state['sovereign_ideology'][:50]}",
        n_results=2,
    )
    trauma_text = format_trauma_for_prompt(memories)

    full_prompt = f"{trauma_text}\n{base_prompt}" if trauma_text else base_prompt

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": full_prompt}],
    )
    decision = response["message"]["content"].strip()

    return {
        "sovereign_last_decision": decision,
        "log": [f"Year {state['year']}: Sovereign decrees — \"{decision}\""],
    }
