"""
Haddock CX Agent — Level 2 Graph Assembly (Data Detective)

Builds the LangGraph StateGraph for the Level 2 "Data Detective" workflow.

Graph topology
──────────────
START → identity_node → reasoner_node ↔ tool_executor_node (ReAct loop, max 5)
                              │
                              ↓  (when LLM stops calling tools, or cap reached)
                        extract_findings_node → l2_draft_node → l2_critic_node
                                                                  ├─ pass → l2_hitl_node
                                                                  └─ fail (≤2) → l2_draft_node  ↺
                                                                       (>2) → l2_hitl_node
                        l2_hitl_node
                          ├─ approve → END
                          └─ request_revision → l2_draft_node  ↺
"""

import logging
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END

from src.config import MAX_REACT_ITERATIONS, MAX_L2_DRAFT_ITERATIONS
from src.state import L2AgentState
from src.nodes.l2 import (
    identity_node,
    reasoner_node,
    tool_executor_node,
    extract_findings_node,
    l2_draft_node,
    l2_critic_node,
    l2_hitl_node,
    l2_escalate_node,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Conditional routing functions
# ──────────────────────────────────────────────────────────────


def route_after_identity(
    state: L2AgentState,
) -> Literal["reasoner_node", "__end__"]:
    """Route after identity resolution.  If restaurant not found, end."""
    if state.get("restaurant_id") is None:
        logger.warning("Identity resolution failed — ending workflow")
        return "__end__"
    return "reasoner_node"


def route_after_reasoner(
    state: L2AgentState,
) -> Literal["tool_executor_node", "extract_findings_node"]:
    """
    Route based on whether the LLM requested tool calls.

    • tool_calls present + budget remains → execute tools
    • no tool_calls OR budget exhausted   → extract findings
    """
    messages = state.get("messages", [])
    react_iters = state.get("react_iterations", 0)

    if messages:
        last_msg = messages[-1]
        tool_calls = getattr(last_msg, "tool_calls", []) or []
        if tool_calls and react_iters < MAX_REACT_ITERATIONS:
            return "tool_executor_node"

    if react_iters >= MAX_REACT_ITERATIONS:
        logger.warning(
            "ReAct iteration cap reached (%d). Extracting findings.",
            react_iters,
        )

    return "extract_findings_node"


def route_after_l2_critic(
    state: L2AgentState,
) -> Literal["l2_hitl_node", "l2_draft_node"]:
    """
    Route based on draft quality and iteration budget.

    • pass            → HITL review
    • fail + budget   → re-draft
    • fail + no budget → HITL with warning
    """
    if state.get("draft_grade") == "pass":
        return "l2_hitl_node"

    draft_iters = state.get("draft_iterations", 0)
    if draft_iters >= MAX_L2_DRAFT_ITERATIONS:
        logger.warning(
            "L2 draft iteration cap reached (%d). Proceeding to HITL.",
            draft_iters,
        )
        return "l2_hitl_node"

    return "l2_draft_node"


def route_after_l2_draft(
    state: L2AgentState,
) -> Literal["l2_critic_node", "l2_hitl_node"]:
    """
    Route after the L2 draft node.

    • If human feedback exists → skip the critic, go directly to HITL.
    • Otherwise → normal path through the L2 critic.
    """
    if state.get("hitl_feedback"):
        logger.info(
            "L2 draft re-generated from human feedback — skipping critic, "
            "routing directly to HITL."
        )
        return "l2_hitl_node"
    return "l2_critic_node"


def route_after_l2_hitl(
    state: L2AgentState,
) -> Literal["l2_draft_node", "__end__"]:
    """
    Route based on the human reviewer's decision.

    • approve          → END
    • request_revision → re-draft with feedback
    """
    if state.get("hitl_decision") == "request_revision":
        logger.info("L2 HITL requested revision — routing back to draft")
        return "l2_draft_node"
    return "__end__"


def route_after_extract_findings(
    state: L2AgentState,
) -> Literal["l2_draft_node", "l2_escalate_node"]:
    """
    Route based on the contents of the investigation.
    If the Reasoner decided it cannot solve the problem, it flags 'ESCALATE_TO_HUMAN'.
    """
    context = state.get("investigation_context", "")
    if "ESCALATE_TO_HUMAN" in context:
        logger.warning(
            "L2 Reasoner triggered ESCALATE_TO_HUMAN — routing to manual escalation."
        )
        return "l2_escalate_node"
    return "l2_draft_node"


# ──────────────────────────────────────────────────────────────
# Graph construction
# ──────────────────────────────────────────────────────────────


def build_l2_graph() -> StateGraph:
    """
    Assemble and return the **compiled** LangGraph for the Level 2
    Data Detective workflow.
    """
    builder = StateGraph(L2AgentState)

    # ── Register nodes ──────────────────────────────────────
    builder.add_node("identity_node", identity_node)
    builder.add_node("reasoner_node", reasoner_node)
    builder.add_node("tool_executor_node", tool_executor_node)
    builder.add_node("extract_findings_node", extract_findings_node)
    builder.add_node("l2_draft_node", l2_draft_node)
    builder.add_node("l2_critic_node", l2_critic_node)
    builder.add_node("l2_hitl_node", l2_hitl_node)
    builder.add_node("l2_escalate_node", l2_escalate_node)

    # ── Edges ───────────────────────────────────────────────

    # Entry point
    builder.add_edge(START, "identity_node")

    # Identity → conditional
    builder.add_conditional_edges(
        "identity_node",
        route_after_identity,
        {
            "reasoner_node": "reasoner_node",
            "__end__": END,
        },
    )

    # Reasoner → conditional (tool calls? or done?)
    builder.add_conditional_edges(
        "reasoner_node",
        route_after_reasoner,
        {
            "tool_executor_node": "tool_executor_node",
            "extract_findings_node": "extract_findings_node",
        },
    )

    # Tool executor → back to reasoner (ReAct loop)
    builder.add_edge("tool_executor_node", "reasoner_node")

    # Extract findings → draft
    builder.add_edge("extract_findings_node", "l2_draft_node")

    # Draft → conditional (skip critic if human feedback exists)
    builder.add_conditional_edges(
        "l2_draft_node",
        route_after_l2_draft,
        {
            "l2_critic_node": "l2_critic_node",
            "l2_hitl_node": "l2_hitl_node",
        },
    )

    # Critic → conditional
    builder.add_conditional_edges(
        "l2_critic_node",
        route_after_l2_critic,
        {
            "l2_hitl_node": "l2_hitl_node",
            "l2_draft_node": "l2_draft_node",
        },
    )

    # HITL → conditional
    builder.add_conditional_edges(
        "l2_hitl_node",
        route_after_l2_hitl,
        {
            "l2_draft_node": "l2_draft_node",
            "__end__": END,
        },
    )

    # ── Compile ─────────────────────────────────────────────
    graph = builder.compile()
    logger.info("✅  L2 Data Detective graph compiled successfully")

    return graph
