"""
Haddock CX Agent — Configuration Module

Centralises environment loading, LLM client initialisation, and Langfuse
setup.  Every other module imports from here — nothing is configured inline.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

# ──────────────────────────────────────────────────────────────
# 1.  Load environment variables
# ──────────────────────────────────────────────────────────────
load_dotenv()

# ──────────────────────────────────────────────────────────────
# 2.  Langfuse — singleton initialisation
#     The Langfuse() constructor registers a global singleton that
#     is later accessed via get_client().
# ──────────────────────────────────────────────────────────────
_langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)


def get_langfuse() -> Langfuse:
    """Return the global Langfuse client (singleton)."""
    return get_client()


def get_langfuse_handler(**kwargs) -> CallbackHandler:
    """
    Create a fresh Langfuse CallbackHandler for LangChain / LangGraph.

    Any extra kwargs (e.g. session_id, user_id, tags) are forwarded to
    the handler constructor.
    """
    return CallbackHandler(**kwargs)


# ──────────────────────────────────────────────────────────────
# 3.  LLM — ChatGroq (llama-3.3-70b-versatile)
# ──────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"],
)

# ──────────────────────────────────────────────────────────────
# 4.  Agentic loop guardrails
# ──────────────────────────────────────────────────────────────
MAX_RETRIEVAL_ITERATIONS: int = 2
MAX_DRAFT_ITERATIONS: int = 2

# Level 2 — Data Detective
MAX_REACT_ITERATIONS: int = 5
MAX_L2_DRAFT_ITERATIONS: int = 2

