"""
Haddock CX Agent — Generation Critic Node

Evaluates the draft CX email against a quality rubric.  If the draft fails,
the critic provides structured feedback that the draft node can use to
improve the next attempt.
"""

import json
import logging

from langchain_core.output_parsers import StrOutputParser

from src.config import llm
from src.prompts import get_generation_critic_prompt
from src.state import CXAgentState

logger = logging.getLogger(__name__)


def generation_critic_node(state: CXAgentState) -> dict:
    """
    Evaluate the draft email.

    Returns
    -------
    dict
        ``{"draft_grade": "pass"|"fail", "feedback": "<critic feedback>"}``
    """
    logger.info("⚖️  Generation Critic Node — evaluating draft")

    prompt = get_generation_critic_prompt()
    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke({
        "user_query": state["user_query"],
        "draft_email": state.get("draft_email", ""),
        "retrieved_context": state.get("retrieved_context", ""),
        "hitl_feedback": state.get("hitl_feedback", "None"),
    })

    # Parse structured JSON or fall back to keyword detection
    try:
        parsed = json.loads(raw_output)
        grade = parsed.get("grade", "fail").lower().strip()
        feedback = parsed.get("feedback", raw_output)
    except (json.JSONDecodeError, AttributeError):
        text = raw_output.lower()
        grade = "pass" if "pass" in text else "fail"
        feedback = raw_output

    grade = grade if grade in ("pass", "fail") else "fail"
    logger.info("⚖️  Generation Critic Node — grade=%s", grade)

    return {
        "draft_grade": grade,
        "feedback": feedback,
    }
