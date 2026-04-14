"""
Haddock CX Agent — Identity Resolution Node (Level 2)

Deterministic lookup — resolves the ``restaurant_id`` for the
customer's email address using the mock database.  No LLM call needed.
"""

import json
import logging

from src.core.mock_db import mock_database
from src.state import L2AgentState

logger = logging.getLogger(__name__)


def identity_node(state: L2AgentState) -> dict:
    """
    Resolve the customer's restaurant identity from their email.

    Returns
    -------
    dict
        ``{"restaurant_id": "rest_XXX"}`` or ``{"status": "escalated"}``
        if the email is not found.
    """
    email = state["user_email"]
    logger.info("🪪  Identity Node — resolving restaurant for: %s", email)

    for restaurant in mock_database["restaurants"]:
        if restaurant["email"].lower() == email.lower():
            restaurant_id = restaurant["restaurant_id"]
            logger.info(
                "🪪  Identity Node — resolved %s → %s (%s)",
                email,
                restaurant_id,
                restaurant["name"],
            )
            return {"restaurant_id": restaurant_id}

    logger.warning("🪪  Identity Node — no restaurant found for %s", email)
    return {"restaurant_id": None, "status": "escalated"}
