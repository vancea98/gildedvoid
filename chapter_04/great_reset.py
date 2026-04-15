"""
Chapter 04 - The Great Reset

When a civilization collapses (stability reaches 0), this module:
1. Uses the AI to summarize the civilization's history into a few sentences
2. Stores that summary in ChromaDB as ancestral memory
3. Returns a fresh world state seeded with trauma from the previous era

This is the mechanic that makes history "a tightening spiral" —
each new civilization starts fresh numerically, but haunted semantically.
"""

import ollama
from chapter_02.world_state import WorldState, create_initial_state
from chapter_04.memory_store import store_collapse, get_trauma, format_trauma_for_prompt


MODEL = "gemma3:4b"

# Tracks how many civilizations have risen and fallen
# In a real implementation this would be stored in the DB; here it's derived from ChromaDB count
def get_current_era(memories_count: int) -> int:
    return memories_count + 1


def summarize_civilization(state: WorldState) -> tuple[str, str]:
    """
    Uses the AI to produce a short summary of the civilization's history
    and identify the primary cause of death.

    Returns: (summary, cause_of_death)
    """
    # Take the last 20 log entries as the history to summarize
    history = "\n".join(state["log"][-20:])

    summary_prompt = f"""A civilization has just collapsed in Year {state['year']}.

Their final ideology was: {state['sovereign_ideology']}
Their final stability: {state['stability']:.0%}
Their final population: {state['population']:,}

Historical record of their final years:
{history}

Write TWO things, separated by a line break:
1. A single sentence summarizing how this civilization lived and died (max 30 words)
2. A single phrase naming the primary cause of collapse (max 8 words)

Example format:
A democratic civilization that turned authoritarian under famine pressure, ultimately destroyed by a cascade of crop failures and popular revolt.
Famine-driven authoritarian collapse"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": summary_prompt}],
    )

    text = response["message"]["content"].strip()
    parts = text.strip().split("\n")

    summary = parts[0].strip() if parts else "A civilization rose and fell."
    cause = parts[-1].strip() if len(parts) > 1 else "Unknown causes"

    return summary, cause


def great_reset(state: WorldState) -> WorldState:
    """
    Executes the Great Reset sequence:
    1. Summarize the fallen civilization
    2. Store it in ancestral memory
    3. Return a new initial state with trauma injected

    The era number is used to give each collapse a unique ID in the database.
    """
    from chapter_04.memory_store import get_client, get_collection
    client = get_client()
    collection = get_collection(client)
    era = collection.count() + 1

    print(f"\n{'=' * 60}")
    print(f"  THE GREAT RESET — Era {era} ends.")
    print(f"  The Architect watches the ashes with mild satisfaction.")
    print(f"{'=' * 60}\n")

    # Step 1: Summarize
    print("[RESET] Summarizing civilization history...")
    summary, cause_of_death = summarize_civilization(state)
    print(f"[RESET] Summary: {summary}")
    print(f"[RESET] Cause: {cause_of_death}")

    # Step 2: Store in ChromaDB
    store_collapse(
        era=era,
        ideology_at_death=state["sovereign_ideology"],
        cause_of_death=cause_of_death,
        summary=summary,
    )

    # Step 3: Build new state with ancestral trauma
    new_state = create_initial_state()

    # Query ancestral memory for what's relevant to this new civilization's starting conditions
    situation_description = (
        f"A new civilization begins with {new_state['population']:,} people "
        f"and moderate food supplies."
    )
    memories = get_trauma(situation_description)
    trauma_text = format_trauma_for_prompt(memories)

    if trauma_text:
        # Inject the trauma into the ideology field as a subtle modifier
        # The Sovereign will read this as part of their "cultural inheritance"
        new_state["sovereign_ideology"] = (
            f"pragmatic democracy — collective welfare above all\n\n{trauma_text}"
        )
        new_state["log"] = [
            f"Era {era + 1}, Year 1: A new civilization awakens on the bones of the old. "
            f"Something feels wrong, though no one can say why."
        ]
        print(f"[RESET] Ancestral trauma injected into new civilization.")
    else:
        new_state["log"] = [
            f"Era {era + 1}, Year 1: A new civilization begins. "
            f"The throne stands empty. The Architect watches."
        ]

    return new_state
