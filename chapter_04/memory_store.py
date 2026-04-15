"""
Chapter 04 - Ancestral Memory Store

A wrapper around ChromaDB that stores and retrieves civilization memories.

Two operations:
  store_collapse()  — called when a civilization dies, saves its history
  get_trauma()      — called when a new civilization starts, retrieves relevant dread

The memories persist across full simulation resets. They are the only thing
that survives the Great Reset — which is exactly the point.
"""

import chromadb
from chromadb.config import Settings


# Path to the ChromaDB database on disk.
# Separate from simulation.db so memories survive even if you --reset the simulation.
MEMORY_DB_PATH = "./ancestral_memory"


def get_client() -> chromadb.PersistentClient:
    """Returns a persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path=MEMORY_DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(client: chromadb.PersistentClient):
    """
    Gets (or creates) the memories collection.

    A ChromaDB 'collection' is like a table — it stores documents,
    their embeddings, and metadata. We use one collection for all
    civilization memories across all resets.
    """
    return client.get_or_create_collection(
        name="civilization_memories",
        # ChromaDB will use its built-in embedding model automatically.
        # For a local setup this is sentence-transformers under the hood.
        metadata={"hnsw:space": "cosine"},  # cosine similarity for semantic search
    )


def store_collapse(era: int, ideology_at_death: str, cause_of_death: str, summary: str):
    """
    Stores a civilization's death record in ancestral memory.

    Called after the Great Reset summarization.

    Args:
        era:              Which simulation reset this was (1st civilization = era 1, etc.)
        ideology_at_death: The Sovereign's ideology when the civilization collapsed
        cause_of_death:   A short description of what caused the collapse
        summary:          The AI-generated summary of the civilization's history
    """
    client = get_client()
    collection = get_collection(client)

    # Each document needs a unique ID
    doc_id = f"era_{era}_collapse"

    collection.add(
        documents=[summary],
        metadatas=[{
            "era": era,
            "ideology_at_death": ideology_at_death,
            "cause_of_death": cause_of_death,
        }],
        ids=[doc_id],
    )

    print(f"[MEMORY] Stored collapse of Era {era} in ancestral memory.")


def get_trauma(current_situation: str, n_results: int = 2) -> list[dict]:
    """
    Retrieves ancestral memories relevant to the current situation.

    Uses semantic search — finds memories whose *meaning* is similar
    to the current situation, even if the exact words differ.

    Args:
        current_situation: A description of what the new civilization is facing
        n_results:         How many memories to retrieve

    Returns:
        A list of dicts with 'summary', 'era', 'ideology_at_death', 'cause_of_death'
    """
    client = get_client()
    collection = get_collection(client)

    # If there are no memories yet, return empty
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[current_situation],
        n_results=min(n_results, collection.count()),
    )

    memories = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        memories.append({
            "summary": doc,
            "era": meta.get("era", "unknown"),
            "ideology_at_death": meta.get("ideology_at_death", "unknown"),
            "cause_of_death": meta.get("cause_of_death", "unknown"),
        })

    return memories


def format_trauma_for_prompt(memories: list[dict]) -> str:
    """
    Formats retrieved memories into text suitable for injecting into a prompt.

    The new Sovereign doesn't know this is "ancestral memory" —
    it's presented as vague inherited cultural dread.
    """
    if not memories:
        return ""

    lines = ["[ANCESTRAL DREAD — fragments of lost eras, felt but not understood]"]
    for m in memories:
        lines.append(f"  - A civilization that believed in '{m['ideology_at_death']}' "
                     f"was destroyed by: {m['cause_of_death']}")
    lines.append("")

    return "\n".join(lines)


def wipe_memories():
    """Deletes all ancestral memory. Used with --reset --wipe-memory flag."""
    import shutil
    import os
    if os.path.exists(MEMORY_DB_PATH):
        shutil.rmtree(MEMORY_DB_PATH)
        print("[MEMORY] Ancestral memory wiped.")
