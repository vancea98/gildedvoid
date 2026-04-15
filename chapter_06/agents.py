"""
Chapter 06 - The Three-Tier Agent Hierarchy

Implements all three agent types:
  Sovereign  (gemma3:4b)  — strategy and ideology
  Chronicles (gemma3:1b)  — narrative translation
  Echoes     (gemma3:1b)  — granular human detail
"""

import ollama

SOVEREIGN_MODEL = "gemma3:4b"
CHRONICLES_MODEL = "gemma3:1b"
ECHOES_MODEL = "gemma3:1b"


# ── The Sovereign ─────────────────────────────────────────────────────────────

def sovereign_decision(
    civ_name: str,
    state: dict,
    trauma_text: str = "",
    decree: str = "",
    throne_held: bool = False,
) -> str:
    """
    The Sovereign thinks strategically about the civilization's situation.
    Returns a single governing decision.
    """
    throne_status = (
        "YOUR CIVILIZATION CONTROLS THE THRONE. Defend it."
        if throne_held else
        "The throne is not yours. Others hold it. This is intolerable."
    )

    prompt = f"""You are the Sovereign of {civ_name}, Year {state['year']}.
Your ideology: {state.get('sovereign_ideology', 'pragmatic governance')}

{throne_status}

WORLD STATE:
- Population: {state.get('population', 0):,}
- Food Supply: {state.get('food_supply', 0):,}
- Stability: {state.get('stability', 0):.0%}

{trauma_text}
{f"[DIVINE DECREE — obey absolutely]: {decree}" if decree else ""}

State ONE specific governing decision for this year. Be concrete. One sentence."""

    response = ollama.chat(
        model=SOVEREIGN_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


# ── The Chronicles ────────────────────────────────────────────────────────────

def chronicles_narration(civ_name: str, year: int, decision: str, stability: float) -> str:
    """
    The Chronicles translate the Sovereign's decision into what the people experience.
    Written from the perspective of a historian of the era.
    """
    mood = "desperation" if stability < 0.3 else "unease" if stability < 0.6 else "cautious hope"

    prompt = f"""You are the royal chronicler of {civ_name}, recording Year {year}.

The Sovereign has decreed: "{decision}"

The public mood is one of {mood}.

Write ONE sentence describing how this decree is experienced by ordinary people.
Be specific and vivid. No preamble."""

    response = ollama.chat(
        model=CHRONICLES_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


# ── The Echoes ────────────────────────────────────────────────────────────────

def echoes_fragment(civ_name: str, year: int, stability: float) -> str:
    """
    The Echoes produce a single fragment of human experience —
    a diary entry, a prayer, a soldier's last words.

    These are called infrequently (every 5 years) to avoid overwhelming the log.
    """
    if stability < 0.2:
        fragment_type = "a desperate prayer"
        context = "The civilization is near collapse."
    elif stability < 0.5:
        fragment_type = "a worried diary entry from a farmer"
        context = "Times are hard but people endure."
    else:
        fragment_type = "a merchant's letter home"
        context = "Life continues with ordinary concerns."

    prompt = f"""Write {fragment_type} from {civ_name} in Year {year}.
{context}
One to two sentences. First person. No preamble. No attribution."""

    response = ollama.chat(
        model=ECHOES_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()
