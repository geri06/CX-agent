# Haddock CX Agent — Nodes package
#
# Re-exports from shared nodes and L1/L2 sub-packages.

# Shared (cross-level) nodes
from src.nodes.router import router_node

# L1 nodes
from src.nodes.l1 import (
    retrieve_node,
    retrieval_critic_node,
    rewrite_query_node,
    draft_node,
    generation_critic_node,
    hitl_node,
    escalate_node,
)

from src.nodes.l2 import (
    identity_node,
    reasoner_node,
    tool_executor_node,
    extract_findings_node,
    l2_draft_node,
    l2_critic_node,
    l2_hitl_node,
)

__all__ = [
    # L1
    "router_node",
    "retrieve_node",
    "retrieval_critic_node",
    "rewrite_query_node",
    "draft_node",
    "generation_critic_node",
    "hitl_node",
    "escalate_node",
    # L2
    "identity_node",
    "reasoner_node",
    "tool_executor_node",
    "extract_findings_node",
    "l2_draft_node",
    "l2_critic_node",
    "l2_hitl_node",
]
