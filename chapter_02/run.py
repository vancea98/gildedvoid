"""
Chapter 02 - Run Your First Agent

This script:
1. Creates the initial world state
2. Builds a simple LangGraph with one node (the Sovereign)
3. Runs it once
4. Prints what happened

Run with: python -m chapter_02.run
"""

from langgraph.graph import StateGraph, END

from chapter_02.world_state import WorldState, create_initial_state
from chapter_02.first_agent import sovereign_node


def build_graph():
    """
    Constructs the LangGraph graph.

    A graph has:
    - A state type (WorldState) — what gets passed between nodes
    - Nodes — functions that process state
    - Edges — connections between nodes

    Right now we have just one node: the Sovereign.
    """

    # Create a new graph builder, telling it what our state looks like
    builder = StateGraph(WorldState)

    # Add the Sovereign as a node
    # "sovereign" is just the name we give it — could be anything
    builder.add_node("sovereign", sovereign_node)

    # Tell the graph where to start
    builder.set_entry_point("sovereign")

    # Tell the graph where to end (after the Sovereign runs, we're done)
    # In Chapter 03, we'll loop back instead of ending
    builder.add_edge("sovereign", END)

    # Compile the graph into a runnable object
    return builder.compile()


def main():
    print("=" * 60)
    print("The Gilded Void — Chapter 02: First Agent")
    print("=" * 60)

    # Create the world
    initial_state = create_initial_state()

    print("\nInitial World State:")
    print(f"  Year:      {initial_state['year']}")
    print(f"  Population:{initial_state['population']:,}")
    print(f"  Stability: {initial_state['stability']:.0%}")
    print(f"  Ideology:  {initial_state['sovereign_ideology']}")

    print("\nCalling the Sovereign... (this may take a few seconds)")
    print("-" * 60)

    # Build and run the graph
    graph = build_graph()
    final_state = graph.invoke(initial_state)

    # Print what happened
    print("\nSovereign's Decision:")
    print(f"  {final_state['sovereign_last_decision']}")

    print("\nFull Historical Log:")
    for entry in final_state["log"]:
        print(f"  {entry}")

    print("\n" + "=" * 60)
    print("Chapter 02 complete.")
    print("Next: Chapter 03 — making this loop forever.")
    print("=" * 60)


if __name__ == "__main__":
    main()
