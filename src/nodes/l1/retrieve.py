"""
Haddock CX Agent — Retrieve Node

Fetches context from the ChromaDB vector store using semantic similarity
search over the ingested CX actuation manual.
"""

import logging

from src.retrieval.vectorstore import retrieve
from src.state import CXAgentState

logger = logging.getLogger(__name__)


def retrieve_node(state: CXAgentState) -> dict:
    """
    Retrieve context relevant to the user's query from ChromaDB.

    Returns
    -------
    dict
        ``{"retrieved_context": "<concatenated top-k chunks>"}``
    """
    query = state["user_query"]
    logger.info("📚  Retrieve Node — querying vector store for: %s", query[:100])

    context = retrieve(query)

    logger.info(
        "📚  Retrieve Node — retrieved %d characters of context",
        len(context),
    )

    return {"retrieved_context": context}
