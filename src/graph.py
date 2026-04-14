"""
Haddock CX Agent — Graph Assembly

Builds the LangGraph StateGraph that implements the CRAG / Self-RAG
workflow for Level 1 customer queries.

Graph topology
──────────────
START ─→ router_node
           ├─ level_1 ─→ retrieve_node ─→ retrieval_critic_node
           │                                ├─ relevant ─→ draft_node ─→ generation_critic_node
           │                                │                             ├─ pass ─→ hitl_node
           │                                │                             └─ fail (≤cap) ─→ draft_node  ↺
           │                                │                                   (>cap) ─→ hitl_node
           │                                └─ irrelevant (≤cap) ─→ rewrite_query_node ─→ retrieve_node  ↺
           │                                         (>cap) ─→ escalate_node ─→ END
           ├─ level_2 ─→ escalate_node ─→ END  (data audit → handled by L2 graph)
           └─ level_3 ─→ escalate_node ─→ END  (out of scope / nonsensical)

           hitl_node
             ├─ approve ─→ END
             └─ request_revision ─→ draft_node  ↺  (draft_iterations reset to 0)
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from src.config import MAX_RETRIEVAL_ITERATIONS, MAX_DRAFT_ITERATIONS
from src.state import CXAgentState
from src.nodes import (
    router_node,
    retrieve_node,
    retrieval_critic_node,
    rewrite_query_node,
    draft_node,
    generation_critic_node,
    hitl_node,
    escalate_node,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Conditional routing functions
# ──────────────────────────────────────────────────────────────


def route_after_router(
    state: CXAgentState,
) -> Literal["retrieve_node", "escalate_node"]:
    """
    Route based on the router's classification.

    • level_1 → retrieve_node (continue L1 pipeline)
    • level_2 → escalate_node (L1 graph exits; main.py dispatches to L2)
    • level_3 → escalate_node (out-of-scope)
    """
    category = state.get("category")
    if category == "level_1":
        return "retrieve_node"
    # level_2 and level_3 both exit through escalate_node.
    # main.py reads `category` from the final state to decide
    # whether to invoke the L2 graph.
    return "escalate_node"


def route_after_retrieval_critic(
    state: CXAgentState,
) -> Literal["draft_node", "rewrite_query_node", "escalate_node"]:
    """
    Route based on context relevance and the retrieval iteration budget.

    • relevant            → proceed to drafting
    • irrelevant + budget → rewrite the query and retry retrieval
    • irrelevant + no budget → escalate
    """
    if state.get("retrieval_grade") == "relevant":
        return "draft_node"

    retrieval_iters = state.get("retrieval_iterations", 0)
    if retrieval_iters >= MAX_RETRIEVAL_ITERATIONS:
        logger.warning(
            "Retrieval iteration cap reached (%d). Escalating.",
            retrieval_iters,
        )
        return "escalate_node"

    return "rewrite_query_node"


def route_after_generation_critic(
    state: CXAgentState,
) -> Literal["hitl_node", "draft_node"]:
    """
    Route based on draft quality and the draft iteration budget.

    • pass            → send to HITL for human approval
    • fail + budget   → re-draft with feedback
    • fail + no budget → send to HITL with warning flag
    """
    if state.get("draft_grade") == "pass":
        return "hitl_node"

    draft_iters = state.get("draft_iterations", 0)
    if draft_iters >= MAX_DRAFT_ITERATIONS:
        logger.warning(
            "Draft iteration cap reached (%d). Proceeding to HITL with warning.",
            draft_iters,
        )
        return "hitl_node"

    return "draft_node"


def route_after_draft(
    state: CXAgentState,
) -> Literal["generation_critic_node", "hitl_node"]:
    """
    Route after the draft node.

    • If human feedback exists → skip the critic, go directly to HITL.
      The human is the final authority; the critic must not overrule them.
    • Otherwise → normal path through the generation critic.
    """
    if state.get("hitl_feedback"):
        logger.info(
            "Draft re-generated from human feedback — skipping critic, "
            "routing directly to HITL for final approval."
        )
        return "hitl_node"
    return "generation_critic_node"


def route_after_hitl(
    state: CXAgentState,
) -> Literal["draft_node", "__end__"]:
    """
    Route based on the human reviewer's decision.

    • approve            → END (send the email)
    • request_revision   → draft_node (with feedback, iterations reset)
    """
    if state.get("hitl_decision") == "request_revision":
        logger.info("HITL requested revision — routing back to draft_node")
        return "draft_node"
    return "__end__"


# ──────────────────────────────────────────────────────────────
# Graph construction
# ──────────────────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """
    Assemble and return the **compiled** LangGraph for the Level-1
    CX workflow.
    """
    builder = StateGraph(CXAgentState)

    # ── Register nodes ──────────────────────────────────────
    builder.add_node("router_node", router_node)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("retrieval_critic_node", retrieval_critic_node)
    builder.add_node("rewrite_query_node", rewrite_query_node)
    builder.add_node("draft_node", draft_node)
    builder.add_node("generation_critic_node", generation_critic_node)
    builder.add_node("hitl_node", hitl_node)
    builder.add_node("escalate_node", escalate_node)

    # ── Edges ───────────────────────────────────────────────

    # Entry point
    builder.add_edge(START, "router_node")

    # Router → conditional
    builder.add_conditional_edges(
        "router_node",
        route_after_router,
        {
            "retrieve_node": "retrieve_node",
            "escalate_node": "escalate_node",
        },
    )

    # Retrieve → critic (always)
    builder.add_edge("retrieve_node", "retrieval_critic_node")

    # Retrieval critic → conditional
    builder.add_conditional_edges(
        "retrieval_critic_node",
        route_after_retrieval_critic,
        {
            "draft_node": "draft_node",
            "rewrite_query_node": "rewrite_query_node",
            "escalate_node": "escalate_node",
        },
    )

    # Rewrite → back to retrieve (loop)
    builder.add_edge("rewrite_query_node", "retrieve_node")

    # Draft → conditional (skip critic if human feedback exists)
    builder.add_conditional_edges(
        "draft_node",
        route_after_draft,
        {
            "generation_critic_node": "generation_critic_node",
            "hitl_node": "hitl_node",
        },
    )

    # Generation critic → conditional
    builder.add_conditional_edges(
        "generation_critic_node",
        route_after_generation_critic,
        {
            "hitl_node": "hitl_node",
            "draft_node": "draft_node",
        },
    )

    # HITL → conditional (approve → END, revision → draft_node)
    builder.add_conditional_edges(
        "hitl_node",
        route_after_hitl,
        {
            "draft_node": "draft_node",
            "__end__": END,
        },
    )

    # Escalate → END (terminal)
    builder.add_edge("escalate_node", END)

    # ── Compile ─────────────────────────────────────────────
    graph = builder.compile()
    logger.info("✅  CX Agent graph compiled successfully")

    return graph
