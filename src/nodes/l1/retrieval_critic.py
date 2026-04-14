"""
Haddock CX Agent — Retrieval Critic Node

Evaluates whether the retrieved context is relevant to the user's query.
Uses a Langfuse-managed prompt to ask the LLM for a binary judgement.
"""

import json
import logging

from langchain_core.output_parsers import StrOutputParser

from src.config import llm
from src.prompts import get_retrieval_critic_prompt
from src.state import CXAgentState

logger = logging.getLogger(__name__)


def retrieval_critic_node(state: CXAgentState) -> dict:
    """
    Grade the retrieved context as ``relevant`` or ``irrelevant``.

    Returns
    -------
    dict
        ``{"retrieval_grade": "relevant"}`` or ``{"retrieval_grade": "irrelevant"}``
    """
    logger.info("🔍  Retrieval Critic Node — grading context relevance")

    prompt = get_retrieval_critic_prompt()
    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke({
        "user_query": state["user_query"],
        "retrieved_context": state.get("retrieved_context", ""),
    })

    # Parse structured JSON or fall back to keyword detection
    try:
        parsed = json.loads(raw_output)
        grade = parsed.get("grade", "irrelevant").lower().strip()
    except (json.JSONDecodeError, AttributeError):
        text = raw_output.lower()
        grade = "relevant" if "relevant" in text else "irrelevant"

    grade = grade if grade in ("relevant", "irrelevant") else "irrelevant"
    logger.info("🔍  Retrieval Critic Node — grade=%s", grade)

    return {"retrieval_grade": grade}
