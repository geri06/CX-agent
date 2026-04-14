"""
Haddock CX Agent — Router Node

Classifies the incoming customer query into:
  - level_1: FAQ / platform usage (self-serve)
  - level_2: Data audit / discrepancy investigation
  - level_3: Out-of-scope / escalation
"""

import json
import logging

from langchain_core.output_parsers import StrOutputParser

from src.config import llm
from src.prompts import get_router_prompt
from src.state import CXAgentState

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"level_1", "level_2", "level_3"}


def router_node(state: CXAgentState) -> dict:
    """
    Classify the customer query into level_1, level_2, or level_3.

    Always runs the LLM classification so the output is visible
    in Langfuse traces.

    Returns
    -------
    dict
        ``{"category": "level_1"|"level_2"|"level_3"}``
    """
    logger.info("🔀  Router Node — classifying query")

    prompt = get_router_prompt()
    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke({"user_query": state["user_query"]})

    # Attempt to parse structured JSON; fall back to keyword detection
    try:
        parsed = json.loads(raw_output)
        category = parsed.get("category", "level_3").lower().strip()
    except (json.JSONDecodeError, AttributeError):
        text = raw_output.lower()
        if "level_1" in text:
            category = "level_1"
        elif "level_2" in text:
            category = "level_2"
        else:
            category = "level_3"

    category = category if category in VALID_CATEGORIES else "level_3"
    logger.info("🔀  Router Node — category=%s", category)

    return {"category": category}
