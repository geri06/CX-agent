"""
Haddock CX Agent — Escalate Node

Terminal node reached when:
  • The router classifies the query as Level 2.
  • The retrieval iteration cap is exhausted without relevant context.
"""

import logging

from src.state import CXAgentState

logger = logging.getLogger(__name__)


def escalate_node(state: CXAgentState) -> dict:
    """
    Mark the workflow as escalated and log the reason.

    Returns
    -------
    dict
        ``{"status": "escalated"}``
    """
    category = state.get("category", "unknown")
    retrieval_iters = state.get("retrieval_iterations", 0)

    if category == "level_2":
        reason = "Query classified as Level 2 (out of scope for self-serve)."
    else:
        reason = (
            f"Retrieval iteration cap reached ({retrieval_iters} rewrites). "
            "Could not find relevant context."
        )

    logger.warning("🚨  Escalate Node — %s", reason)
    logger.info(
        "🚨  Escalate Node — routing to human CX team | query: %s",
        state.get("user_query", ""),
    )

    return {"status": "escalated"}
