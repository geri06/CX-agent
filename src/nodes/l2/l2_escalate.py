"""
Haddock CX Agent — L2 Escalate Node

Terminal node for the L2 Data Detective when it cannot resolve the data discrepancy
or determine the root cause, requiring human intervention.
"""

import logging

from src.state import L2AgentState

logger = logging.getLogger(__name__)


def l2_escalate_node(state: L2AgentState) -> dict:
    """
    Mark the L2 workflow as escalated.

    Returns
    -------
    dict
        ``{"status": "escalated"}``
    """
    context = state.get("investigation_context", "No context provided.")
    logger.warning("🚨  L2 Escalate Node — Data Detective could not solve.")
    logger.info("🚨  Escalate Reason: %s", context)

    return {"status": "escalated"}
