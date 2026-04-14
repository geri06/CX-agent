"""
Haddock CX Agent — Graph State Definitions

Uses TypedDict so that LangGraph can automatically merge partial
updates returned by each node.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class CXAgentState(TypedDict):
    """State schema shared by every node in the Level-1 CX workflow."""

    # ── Inputs ──────────────────────────────────────────────
    user_query: str
    """The customer's original (or rewritten) query."""

    user_email: Optional[str]
    """The customer's email address."""

    user_name: Optional[str]
    """The customer's name (or restaurant name)."""

    # ── Classification ──────────────────────────────────────
    category: Optional[str]
    """'level_1' or 'level_2' — set by the router node."""

    # ── Retrieval ───────────────────────────────────────────
    retrieved_context: Optional[str]
    """Context fetched from the knowledge base (ChromaDB)."""

    retrieval_grade: Optional[str]
    """'relevant' or 'irrelevant' — set by retrieval critic node."""

    # ── Drafting ────────────────────────────────────────────
    draft_email: Optional[str]
    """The current CX email draft."""

    draft_grade: Optional[str]
    """'pass' or 'fail' — set by generation critic node."""

    feedback: Optional[str]
    """Feedback from the generation critic or HITL reviewer for draft improvement."""

    # ── Loop counters ───────────────────────────────────────
    retrieval_iterations: int
    """How many times the query has been rewritten for retrieval."""

    draft_iterations: int
    """How many times the draft has been regenerated."""

    # ── HITL (Human-In-The-Loop) ────────────────────────────
    hitl_decision: Optional[str]
    """
    Human reviewer's decision:
      'approve'            — draft is good, send the email
      'request_revision'   — draft needs changes, send feedback back to draft node
    """

    hitl_feedback: Optional[str]
    """Free-text feedback from the human reviewer (used when hitl_decision = 'request_revision')."""

    # ── Terminal ────────────────────────────────────────────
    status: str
    """
    Workflow outcome:
      'in_progress'           — still running
      'escalated'             — routed to human CX team
      'approved'              — HITL approved
      'approved_with_warning' — HITL approved but draft hit iteration cap
    """


# ──────────────────────────────────────────────────────────────
# Level 2 — Data Detective State
# ──────────────────────────────────────────────────────────────


class L2AgentState(TypedDict):
    """State schema for the Level-2 'Data Detective' workflow.

    Uses a ReAct agent loop with LangChain messages, then feeds
    investigation results into a Draft → Critic → HITL pipeline.
    """

    # ── Inputs ──────────────────────────────────────────────
    user_query: str
    """The customer's original complaint about data discrepancies."""

    user_email: str
    """Email address used to resolve the restaurant identity."""

    user_name: Optional[str]
    """The customer's name."""

    # ── Identity Resolution ─────────────────────────────────
    restaurant_id: Optional[str]
    """Resolved from ``user_email`` via the identity node."""

    # ── ReAct Loop ──────────────────────────────────────────
    messages: Annotated[list, add_messages]
    """LangChain message history driving the ReAct reasoning loop."""

    react_iterations: int
    """How many reasoner → tool-executor cycles have run."""

    investigation_context: Optional[str]
    """Accumulated investigation findings (ground truth for the draft)."""

    # ── Drafting ────────────────────────────────────────────
    draft_email: Optional[str]
    """The current resolution email draft."""

    draft_grade: Optional[str]
    """'pass' or 'fail' — set by the L2 generation critic node."""

    feedback: Optional[str]
    """Feedback from the L2 critic or HITL reviewer."""

    draft_iterations: int
    """How many times the draft has been regenerated."""

    # ── HITL ────────────────────────────────────────────────
    hitl_decision: Optional[str]
    """Human reviewer's decision: 'approve' or 'request_revision'."""

    hitl_feedback: Optional[str]
    """Free-text feedback from the human reviewer."""

    # ── Terminal ────────────────────────────────────────────
    status: str
    """Workflow outcome: 'in_progress', 'escalated', 'approved', 'approved_with_warning'."""

