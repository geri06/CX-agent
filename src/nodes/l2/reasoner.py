"""
Haddock CX Agent — Reasoner Node (Level 2 ReAct)

The "thinking" node in the ReAct loop.  Fetches the system prompt from
Langfuse, binds the investigation tools to the LLM, and invokes it with
the accumulated message history.  The LLM either returns tool calls
(continue investigating) or a final text summary (done).
"""

import logging

from langchain_core.messages import SystemMessage

from src.config import llm
from src.core.tools import INVESTIGATION_TOOLS
from src.prompts import get_l2_reasoner_prompt
from src.state import L2AgentState

logger = logging.getLogger(__name__)


def reasoner_node(state: L2AgentState) -> dict:
    """
    Run one iteration of the ReAct reasoner.

    1. Prepend the Langfuse system prompt (with ``restaurant_id``) to
       the message history.
    2. Invoke the LLM with bound tools.
    3. Return the AI response (may contain tool_calls or a final summary).

    Returns
    -------
    dict
        ``{"messages": [ai_message], "react_iterations": N+1}``
    """
    current_iter = state.get("react_iterations", 0)
    logger.info("🧠  Reasoner Node — iteration %d", current_iter)

    # Fetch system prompt from Langfuse and format it
    prompt_template = get_l2_reasoner_prompt()
    formatted = prompt_template.format_messages(
        restaurant_id=state.get("restaurant_id", "unknown"),
    )

    # Prepend system prompt to the accumulated conversation
    system_msg = formatted[0] if formatted else SystemMessage(content="Investigate.")
    all_messages = [system_msg] + list(state.get("messages", []))

    # Bind tools and invoke
    llm_with_tools = llm.bind_tools(INVESTIGATION_TOOLS)
    response = llm_with_tools.invoke(all_messages)

    tool_calls = getattr(response, "tool_calls", []) or []
    if tool_calls:
        logger.info(
            "🧠  Reasoner Node — requesting %d tool call(s): %s",
            len(tool_calls),
            [tc["name"] for tc in tool_calls],
        )
    else:
        logger.info(
            "🧠  Reasoner Node — investigation complete, summary length: %d",
            len(response.content or ""),
        )

    return {
        "messages": [response],
        "react_iterations": current_iter + 1,
    }
