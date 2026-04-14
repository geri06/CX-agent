"""
Haddock CX Agent — Rewrite Query Node

When the retrieval critic marks context as irrelevant, this node rewrites
the user's query to improve the next retrieval attempt.
"""

import logging

from langchain_core.output_parsers import StrOutputParser

from src.config import llm
from src.prompts import get_rewrite_query_prompt
from src.state import CXAgentState

logger = logging.getLogger(__name__)


def rewrite_query_node(state: CXAgentState) -> dict:
    """
    Rewrite the query for better retrieval and increment the iteration
    counter.

    Returns
    -------
    dict
        Updated ``user_query`` and incremented ``retrieval_iterations``.
    """
    current_iter = state.get("retrieval_iterations", 0)
    logger.info(
        "✏️  Rewrite Query Node — iteration %d → %d",
        current_iter,
        current_iter + 1,
    )

    prompt = get_rewrite_query_prompt()
    chain = prompt | llm | StrOutputParser()

    rewritten_query = chain.invoke({
        "user_query": state["user_query"],
        "retrieved_context": state.get("retrieved_context", ""),
    })

    rewritten_query = rewritten_query.strip()
    logger.info("✏️  Rewrite Query Node — new query: %s", rewritten_query[:120])

    return {
        "user_query": rewritten_query,
        "retrieval_iterations": current_iter + 1,
    }
