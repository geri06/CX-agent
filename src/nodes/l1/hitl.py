"""
Haddock CX Agent — HITL (Human-In-The-Loop) Node

Simulates a human CX agent reviewing and making a decision on the draft
email.  The reviewer can:

  1. **Approve** — the draft is sent as-is.
  2. **Request revision** — provide feedback and send the draft back to
     the draft node for regeneration. This resets ``draft_iterations``
     to 0 so the self-correction loop gets a fresh budget.

In production, replace the mock logic with ``langgraph.interrupt()`` or
an async callback mechanism (e.g. webhook) that pauses the graph and
waits for real human input.
"""

import logging

from src.config import MAX_DRAFT_ITERATIONS
from src.state import CXAgentState

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Mock configuration
# ──────────────────────────────────────────────────────────────
# Change this to "request_revision" to test the feedback loop path.
# In production, the decision comes from the actual human reviewer.
MOCK_DECISION: str = "request_revision" # approve | request_revision
MOCK_FEEDBACK: str = (
    "Please make the tone more empathetic in the opening paragraph "
    "and add a specific step-by-step guide for the guest."
)


def hitl_node(state: CXAgentState) -> dict:
    """
    Simulate human review of the draft email via terminal input.
    Combines new human feedback with existing generation critic feedback.

    Returns
    -------
    dict
        When **approving**:
            ``{"status": "approved", "hitl_decision": "approve"}``
            or ``{"status": "approved_with_warning", ...}`` if the draft
            reached the critic iteration cap.

        When **requesting revision**:
            ``{"hitl_decision": "request_revision",
              "feedback": "<combined feedback>",
              "draft_iterations": 0,
              "status": "in_progress"}``
            The ``draft_iterations`` counter is reset to 0 so the
            draft → generation_critic loop gets a fresh budget.
    """
    draft_iters = state.get("draft_iterations", 0)
    draft_grade = state.get("draft_grade", "pass")

    # ── Terminal UI for Human Review ────────────────────────
    print("\n" + "═" * 80)
    print("👤 INTERRUPT: HUMAN-IN-THE-LOOP (HITL) REVIEW REQUIRED")
    print("═" * 80)
    print(f"Customer Query: {state.get('user_query')}")
    print("─" * 80)
    print("Draft Email:")
    print(state.get("draft_email"))
    print("═" * 80)

    # Check if a decision was injected by the API (via update_state)
    pre_decision = state.get("hitl_decision")
    if pre_decision in ["approve", "request_revision"]:
        decision = pre_decision
        if decision == "request_revision":
            human_feedback = state.get("hitl_feedback", "")
        else:
            human_feedback = ""
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
        
        # Combine existing critic feedback with human feedback
        previous_feedback = state.get("feedback", "")
        if previous_feedback:
            combined_feedback = f"{previous_feedback}\n\n[Human Reviewer Feedback]: {human_feedback}"
        else:
            combined_feedback = f"[Human Reviewer Feedback]: {human_feedback}"

        logger.info(
            "👤  HITL Node — human requested revision with feedback: %s",
            human_feedback[:120],
        )
        return {
            "hitl_decision": "request_revision",
            "feedback": combined_feedback,
            "hitl_feedback": human_feedback,
            "draft_iterations": 0,       # ← Reset counter for fresh loop budget
            "status": "in_progress",
        }

    # ── Path B: Approve ─────────────────────────────────────
    if draft_grade != "pass" and draft_iters >= MAX_DRAFT_ITERATIONS:
        status = "approved_with_warning"
        logger.warning(
            "👤  HITL Node — draft did NOT pass critic after %d iterations. "
            "Flagging for extra human review.",
            draft_iters,
        )
    else:
        status = "approved"
        logger.info("👤  HITL Node — draft approved by human reviewer")

    logger.info(
        "👤  HITL Node — status=%s | draft preview: %s…",
        status,
        (state.get("draft_email") or "")[:100].replace("\n", " "),
    )

    return {
        "status": status,
        "hitl_decision": "approve",
    }
