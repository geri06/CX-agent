"""
Haddock CX Agent — HITL Node (Level 2 — Data Detective)

Interactive terminal-based human review for the Level 2 resolution
email.  Supports approve or request_revision with feedback combination.
"""

import logging

from src.config import MAX_L2_DRAFT_ITERATIONS
from src.state import L2AgentState

logger = logging.getLogger(__name__)


def l2_hitl_node(state: L2AgentState) -> dict:
    """
    Interactive human review of the Level 2 draft email via terminal.
    Combines new human feedback with existing critic feedback.

    Returns
    -------
    dict
        Approval or revision request with combined feedback.
    """
    draft_iters = state.get("draft_iterations", 0)
    draft_grade = state.get("draft_grade", "pass")

    # ── Terminal UI ─────────────────────────────────────────
    print("\n" + "═" * 80)
    print("👤 INTERRUPT: LEVEL 2 HITL REVIEW — DATA INVESTIGATION")
    print("═" * 80)
    print(f"Customer Query: {state.get('user_query')}")
    print("─" * 80)
    print("Investigation Findings:")
    print((state.get("investigation_context") or "")[:500])
    print("─" * 80)
    print("Draft Email:")
    print(state.get("draft_email"))
    print("═" * 80)

    # Check if a decision was injected by the API (via update_state)
    pre_decision = state.get("hitl_decision")
    if pre_decision in ["approve", "request_revision"]:
        decision = pre_decision
        human_feedback = state.get("hitl_feedback", "")
    else:
        while True:
            review_input = input("\nApprove this draft? (y/n): ").strip().lower()
            if review_input in ["y", "yes", "n", "no"]:
                break
            print("Please enter 'y' to approve or 'n' to request revision.")

        decision = "approve" if review_input in ["y", "yes"] else "request_revision"
        
        if decision == "request_revision":
            human_feedback = input("\nEnter feedback to improve the draft: ").strip()
        else:
            human_feedback = ""

    # ── Path A: Request revision ────────────────────────────
    if decision == "request_revision":
        previous_feedback = state.get("feedback", "")
        if previous_feedback:
            combined_feedback = (
                f"{previous_feedback}\n\n[Human Reviewer Feedback]: {human_feedback}"
            )
        else:
            combined_feedback = f"[Human Reviewer Feedback]: {human_feedback}"

        logger.info(
            "👤  L2 HITL Node — revision requested: %s", human_feedback[:120]
        )
        return {
            "hitl_decision": "request_revision",
            "feedback": combined_feedback,
            "hitl_feedback": human_feedback,
            "draft_iterations": 0,
            "status": "in_progress",
        }

    # ── Path B: Approve ─────────────────────────────────────
    if draft_grade != "pass" and draft_iters >= MAX_L2_DRAFT_ITERATIONS:
        status = "approved_with_warning"
        logger.warning(
            "👤  L2 HITL Node — draft did NOT pass critic after %d iters.",
            draft_iters,
        )
    else:
        status = "approved"
        logger.info("👤  L2 HITL Node — draft approved")

    return {
        "status": status,
        "hitl_decision": "approve",
    }
