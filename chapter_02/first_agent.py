"""
Chapter 02 - The Sovereign Agent

This is our first AI agent: the Sovereign.
It receives the current world state and decides what to do next.

In The Gilded Void, the Sovereign is the "intellect of the state" —
the ruling mind that manages long-term strategy and survival.

For now it does one simple thing: observe the world and produce a decision.
"""

import ollama
from chapter_02.world_state import WorldState


# The model we're using. We pulled this in Chapter 01.
MODEL = "gemma3:4b"


def build_sovereign_prompt(state: WorldState) -> str:
    """
    Constructs the text we send to the AI model.

    This is called a "prompt" — it defines the agent's identity,
    its current situation, and what we want it to do.

    The quality of your simulation depends heavily on prompt design.
    """
    return f"""You are the Sovereign of a civilization in Year {state['year']}.
Your ideology: {state['sovereign_ideology']}

CURRENT WORLD STATE:
- Population: {state['population']:,}
- Food Supply: {state['food_supply']:,} units
- Stability: {state['stability']:.0%}

RECENT HISTORY:
{chr(10).join(f'  - {entry}' for entry in state['log'][-5:])}

Based on this situation, state ONE specific governing decision you will make this year.
Be concrete. One sentence. No preamble."""


def sovereign_node(state: WorldState) -> dict:
    """
    The Sovereign node — the core decision-making agent.

    LangGraph calls this function with the current world state.
    We send that state to the AI model and return its decision.

    Returns a partial state update: only the fields we're changing.
    """

    # Build the prompt from the current state
    prompt = build_sovereign_prompt(state)

    # Call the local AI model via Ollama
    # ollama.chat() sends a conversation and returns the model's reply
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    # Extract the text of the response
    decision = response["message"]["content"].strip()

    # Create a log entry for this year's decision
    log_entry = f"Year {state['year']}: Sovereign decrees — \"{decision}\""

    # Return only the fields we're updating.
    # LangGraph will merge this with the existing state automatically.
    # Because `log` uses operator.add, our new entry gets APPENDED, not replacing the list.
    return {
        "sovereign_last_decision": decision,
        "log": [log_entry],
    }
