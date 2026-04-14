"""
Haddock CX Agent — Langfuse Prompt Helpers

Thin wrappers around langfuse.get_prompt() that fetch prompts by name and
compile them into LangChain-compatible ChatPromptTemplates.

╔══════════════════════════════════════════════════════════════╗
║  IMPORTANT — No prompts are hardcoded in this repository.   ║
║  All prompts must exist in the Langfuse UI (or be seeded    ║
║  via scripts/seed_prompts.py) BEFORE running the agent.     ║
╚══════════════════════════════════════════════════════════════╝
"""

from langchain_core.prompts import ChatPromptTemplate

from src.config import get_langfuse


# ──────────────────────────────────────────────────────────────
# Generic fetcher
# ──────────────────────────────────────────────────────────────

def get_chat_prompt(prompt_name: str) -> ChatPromptTemplate:
    """
    Fetch a **chat** prompt from Langfuse by name, convert it to a
    LangChain ``ChatPromptTemplate`` and return it.

    The Langfuse prompt must use ``{{variable}}`` syntax; the helper
    ``get_langchain_prompt()`` converts them to ``{variable}`` for
    LangChain.
    """
    langfuse = get_langfuse()
    langfuse_prompt = langfuse.get_prompt(prompt_name, type="chat")
    langchain_messages = langfuse_prompt.get_langchain_prompt()
    return ChatPromptTemplate.from_messages(langchain_messages)


# ──────────────────────────────────────────────────────────────
# Per-node convenience accessors (documents expected prompts)
# ──────────────────────────────────────────────────────────────

def get_router_prompt() -> ChatPromptTemplate:
    """Prompt: cx-router  |  Variables: {{user_query}}"""
    return get_chat_prompt("cx-router")


def get_retrieval_critic_prompt() -> ChatPromptTemplate:
    """Prompt: cx-retrieval-critic  |  Variables: {{user_query}}, {{retrieved_context}}"""
    return get_chat_prompt("cx-retrieval-critic")


def get_rewrite_query_prompt() -> ChatPromptTemplate:
    """Prompt: cx-rewrite-query  |  Variables: {{user_query}}, {{retrieved_context}}"""
    return get_chat_prompt("cx-rewrite-query")


def get_draft_email_prompt() -> ChatPromptTemplate:
    """Prompt: cx-draft-email  |  Variables: {{user_query}}, {{retrieved_context}}, {{feedback}}"""
    return get_chat_prompt("cx-draft-email")


def get_generation_critic_prompt() -> ChatPromptTemplate:
    """Prompt: cx-generation-critic  |  Variables: {{user_query}}, {{draft_email}}, {{retrieved_context}}"""
    return get_chat_prompt("cx-generation-critic")


# ──────────────────────────────────────────────────────────────
# Level 2 — Data Detective prompts
# ──────────────────────────────────────────────────────────────

def get_l2_reasoner_prompt() -> ChatPromptTemplate:
    """Prompt: l2-reasoner  |  Variables: {{restaurant_id}}"""
    return get_chat_prompt("l2-reasoner")


def get_l2_draft_email_prompt() -> ChatPromptTemplate:
    """Prompt: l2-draft-email  |  Variables: {{user_query}}, {{investigation_context}}, {{feedback}}"""
    return get_chat_prompt("l2-draft-email")


def get_l2_generation_critic_prompt() -> ChatPromptTemplate:
    """Prompt: l2-generation-critic  |  Variables: {{user_query}}, {{draft_email}}, {{investigation_context}}, {{hitl_feedback}}"""
    return get_chat_prompt("l2-generation-critic")

