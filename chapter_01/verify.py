"""
Chapter 01 - Environment Verification
Run this script to confirm everything is installed correctly.
Usage: python chapter_01/verify.py
"""

import sys

def check(label, fn):
    """Run a check function and print the result."""
    try:
        result = fn()
        print(f"[OK] {label}" + (f": {result}" if result else ""))
        return True
    except Exception as e:
        print(f"[FAIL] {label}: {e}")
        return False


def check_python():
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info < (3, 10):
        raise RuntimeError(f"Need Python 3.10+, got {version}")
    return f"Python {version}"


def check_langgraph():
    from langgraph.graph import StateGraph
    import importlib.metadata
    version = importlib.metadata.version("langgraph")
    return f"LangGraph {version}"


def check_chromadb():
    import chromadb
    return f"ChromaDB {chromadb.__version__}"


def check_ollama_client():
    import ollama
    return "ollama client imported"


def check_ollama_running():
    import ollama
    # list() returns the models currently available locally
    models = ollama.list()
    names = [m.model for m in models.models]
    if not names:
        raise RuntimeError("Ollama is running but no models are downloaded. Run: ollama pull gemma3:4b")
    # Check specifically for our target model
    target = "gemma3:4b"
    available = [n for n in names if target in n]
    if not available:
        raise RuntimeError(
            f"Model '{target}' not found. Available: {names}\n"
            f"Run: ollama pull {target}"
        )
    return f"Ollama running, {target} available"


if __name__ == "__main__":
    print("=" * 50)
    print("Gilded Void — Environment Check")
    print("=" * 50)

    results = [
        check("Python version", check_python),
        check("LangGraph", check_langgraph),
        check("ChromaDB", check_chromadb),
        check("Ollama Python client", check_ollama_client),
        check("Ollama running + model ready", check_ollama_running),
    ]

    print("=" * 50)
    if all(results):
        print("All checks passed. You're ready for Chapter 02.")
    else:
        failed = results.count(False)
        print(f"{failed} check(s) failed. Fix the issues above before continuing.")
    print("=" * 50)
