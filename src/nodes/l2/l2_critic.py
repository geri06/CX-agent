"""
Haddock CX Agent — Generation Critic Node (Level 2 — Data Detective)

Evaluates the draft resolution email against the investigation findings
(ground truth) to ensure no hallucinations and proper tone.
Uses the ``l2-generation-critic`` prompt from Langfuse.
"""

import json
import logging

from langchain_core.output_parsers import StrOutputParser

from src.config import llm
from src.prompts import get_l2_generation_critic_prompt
from src.state import L2AgentState

logger = logging.getLogger(__name__)


def l2_critic_node(state: L2AgentState) -> dict:
    """
    Evaluate the L2 draft email against investigation findings.

    Returns
    -------
    dict
        ``{"draft_grade": "pass"|"fail", "feedback": "<critic feedback>"}``
    """
    logger.info("⚖️  L2 Critic Node — evaluating draft")

    prompt = get_l2_generation_critic_prompt()
    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke({
        "user_query": state["user_query"],
        "draft_email": state.get("draft_email", ""),
        "investigation_context": state.get("investigation_context", ""),
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
    logger.info("⚖️  L2 Critic Node — grade=%s", grade)

    return {
        "draft_grade": grade,
        "feedback": feedback,
    }
