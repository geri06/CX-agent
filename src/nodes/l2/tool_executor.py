"""
Haddock CX Agent — Tool Executor Node (Level 2 ReAct)

Executes the tool calls requested by the reasoner and returns
``ToolMessage`` results back into the message history.
"""

import logging

from langchain_core.messages import ToolMessage

from src.core.tools import TOOL_REGISTRY
from src.state import L2AgentState

logger = logging.getLogger(__name__)


def tool_executor_node(state: L2AgentState) -> dict:
    """
    Execute every tool call in the last AI message.

    Returns
    -------
    dict
        ``{"messages": [ToolMessage, ...]}``
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", []) or []

    tool_messages = []
    for tc in tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]
        logger.info("🔧  Tool Executor — calling %s(%s)", tool_name, tool_args)

        tool_fn = TOOL_REGISTRY.get(tool_name)
        if tool_fn is None:
            result = f"Error: unknown tool '{tool_name}'"
            logger.error("🔧  Tool Executor — %s", result)
        else:
            result = tool_fn.invoke(tool_args)

        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tc["id"],
            )
        )
        logger.info(
            "🔧  Tool Executor — %s result length: %d chars",
            tool_name,
            len(str(result)),
        )

    return {"messages": tool_messages}
