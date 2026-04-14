"""
Haddock CX Agent — Draft Node (Level 1)

Generates a professional CX email response using the user's query,
retrieved context, and any feedback from a prior generation-critic review.

When HUMAN feedback is present (post-HITL revision), the node switches
to an "edit-only" mode: it takes the current draft as a base and applies
ONLY the human's requested changes, preserving everything else.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config import llm
from src.core.mock_db import mock_database
from src.prompts import get_draft_email_prompt
from src.state import CXAgentState

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Human-revision prompt (used ONLY after HITL feedback)
# ──────────────────────────────────────────────────────────────

HUMAN_REVISION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a support email editor at haddock. A human reviewer has "
        "requested specific changes to a previously drafted email.\n\n"
        "CRITICAL RULES:\n"
        "1. Take the CURRENT DRAFT below as your base.\n"
        "2. Apply ONLY the changes the human reviewer requested.\n"
        "3. Do NOT remove, rephrase, or restructure any part of the email "
        "that the human did NOT mention.\n"
        "4. Do NOT add new information beyond what the human asked for.\n"
        "5. Keep the exact same structure, tone, greeting, and sign-off "
        "unless the human explicitly asked to change them.\n"
        "6. Output ONLY the revised email body. No explanations."
    ),
    (
        "user",
        "CURRENT DRAFT:\n{current_draft}\n\n"
        "HUMAN FEEDBACK:\n{human_feedback}\n\n"
        "Apply the human's changes to the draft above and output the "
        "revised email."
    ),
])


def draft_node(state: CXAgentState) -> dict:
    """
    Draft (or re-draft) the CX email response.

    Two modes:
    1. **Normal draft** — uses the standard prompt with query + context + feedback.
    2. **Human revision** — if ``hitl_feedback`` is set, takes the current
       draft and applies ONLY the human's requested changes.

    Returns
    -------
    dict
        Updated ``draft_email`` and incremented ``draft_iterations``.
    """
    current_iter = state.get("draft_iterations", 0)
    hitl_feedback = state.get("hitl_feedback")

    # ── Mode 2: Human revision (surgical edit) ───────────────
    if hitl_feedback and state.get("draft_email"):
        logger.info(
            "📝  Draft Node — HUMAN REVISION mode (iteration %d)",
            current_iter,
        )

        chain = HUMAN_REVISION_PROMPT | llm | StrOutputParser()
        draft = chain.invoke({
            "current_draft": state["draft_email"],
            "human_feedback": hitl_feedback,
        })

        draft = draft.strip()
        logger.info("📝  Draft Node — revised draft length: %d chars", len(draft))

        return {
            "draft_email": draft,
            "draft_iterations": current_iter + 1,
        }

    # ── Mode 1: Normal draft (from scratch / critic feedback) ─
    logger.info("📝  Draft Node — generating draft (iteration %d)", current_iter)

    user_name = state.get("user_name", "Valued Customer")
    first_name = user_name.split()[0] if user_name else "Valued Customer"
    logger.info("📝  Draft Node — addressing: %s", first_name)

    prompt = get_draft_email_prompt()
    chain = prompt | llm | StrOutputParser()

    draft = chain.invoke({
        "user_query": state["user_query"],
        "retrieved_context": state.get("retrieved_context", ""),
        "feedback": state.get("feedback", "No prior feedback."),
        "user_name": first_name,
    })

    draft = draft.strip()
    logger.info("📝  Draft Node — draft length: %d chars", len(draft))

    return {
        "draft_email": draft,
        "draft_iterations": current_iter + 1,
    }
