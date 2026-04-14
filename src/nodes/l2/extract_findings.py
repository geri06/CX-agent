"""
Haddock CX Agent — Extract Findings Node (Level 2)

Runs after the ReAct loop finishes.  Extracts the investigation summary
from the last AI message (or compiles tool results if the loop hit the
iteration cap) and writes it to ``investigation_context``.
"""

import logging

from langchain_core.messages import AIMessage, ToolMessage

from src.state import L2AgentState

logger = logging.getLogger(__name__)


def extract_findings_node(state: L2AgentState) -> dict:
    """
    Extract investigation findings into ``investigation_context``.

    Returns
    -------
    dict
        ``{"investigation_context": "<findings text>"}``
    """
    messages = state.get("messages", [])

    # Try to get the last AI message content (the reasoner's summary)
    last_ai_content = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai_content = msg.content or ""
            break

    # If the last AI message has content, use it as the summary
    if last_ai_content.strip():
        investigation_context = last_ai_content
    else:
        # Fallback: compile all tool results
        tool_results = [
            msg.content for msg in messages if isinstance(msg, ToolMessage)
        ]
        investigation_context = "\n\n---\n\n".join(tool_results) or "No findings."

    logger.info(
        "📋  Extract Findings Node — context length: %d chars",
        len(investigation_context),
    )

    return {"investigation_context": investigation_context}
