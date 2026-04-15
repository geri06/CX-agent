"""
Haddock CX Agent — API Server

FastAPI backend that serves:
  1. Mock database endpoints (GET /api/db/{collection})
  2. Agent execution via SSE streaming (POST /api/run-agent)
     The agent first runs the Router node to classify the query,
     then dispatches to L1 (FAQ), L2 (Data Detective), or L3 (escalation).

Usage:
    uv run uvicorn api_server:app --reload --port 8000
"""

import json
import logging
import asyncio
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage

from src.core.mock_db import mock_database
from src.config import get_langfuse_handler
from src.graph import build_graph         # L1 graph (includes router)
from src.l2_graph import build_l2_graph   # L2 Data Detective graph
from src.nodes.router import router_node  # standalone router for classification

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("haddock-api")

# ──────────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────────
app = FastAPI(title="Haddock CX Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Node metadata for human-readable labels
# ──────────────────────────────────────────────────────────────
NODE_META = {
    # ── Router ─────────────────────────────────────────────
    "router_node": {
        "label": "Query Router",
        "description": "Classifying query into L1/L2/L3...",
        "type": "reasoner",
    },
    # ── L1 nodes ───────────────────────────────────────────
    "retrieve_node": {
        "label": "Knowledge Retrieval",
        "description": "Searching knowledge base for relevant context...",
        "type": "tool",
    },
    "retrieval_critic_node": {
        "label": "Retrieval Critic",
        "description": "Evaluating context relevance...",
        "type": "reasoner",
    },
    "rewrite_query_node": {
        "label": "Query Rewrite",
        "description": "Improving search query...",
        "type": "reasoner",
    },
    "draft_node": {
        "label": "Draft Email",
        "description": "Composing customer response email...",
        "type": "reasoner",
    },
    "generation_critic_node": {
        "label": "Quality Critic",
        "description": "Evaluating draft quality...",
        "type": "reasoner",
    },
    "hitl_node": {
        "label": "Human Review",
        "description": "Awaiting human-in-the-loop approval...",
        "type": "system",
    },
    "escalate_node": {
        "label": "Escalation",
        "description": "Escalating to human support...",
        "type": "system",
    },
    # ── L2 nodes ───────────────────────────────────────────
    "identity_node": {
        "label": "Identity Resolution",
        "description": "Resolving restaurant from email...",
        "type": "tool",
    },
    "reasoner_node": {
        "label": "Reasoner",
        "description": "Analyzing data and deciding next action...",
        "type": "reasoner",
    },
    "tool_executor_node": {
        "label": "Tool Executor",
        "description": "Executing investigation tools...",
        "type": "tool",
    },
    "extract_findings_node": {
        "label": "Extract Findings",
        "description": "Summarizing investigation results...",
        "type": "reasoner",
    },
    "l2_draft_node": {
        "label": "Draft Email",
        "description": "Composing customer response email...",
        "type": "reasoner",
    },
    "l2_critic_node": {
        "label": "Quality Critic",
        "description": "Evaluating draft quality...",
        "type": "reasoner",
    },
    "l2_hitl_node": {
        "label": "Human Review",
        "description": "Awaiting human-in-the-loop approval...",
        "type": "system",
    },
    "l2_escalate_node": {
        "label": "Escalation",
        "description": "Escalating to human support...",
        "type": "system",
    },
}


# ──────────────────────────────────────────────────────────────
# Mock Database endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/api/db/restaurants")
async def get_restaurants():
    return {"data": mock_database["restaurants"], "count": len(mock_database["restaurants"])}


@app.get("/api/db/invoices")
async def get_invoices():
    return {"data": mock_database["invoices"], "count": len(mock_database["invoices"])}


@app.get("/api/db/ingredients")
async def get_ingredients():
    return {"data": mock_database["ingredients"], "count": len(mock_database["ingredients"])}


@app.get("/api/db/recipes")
async def get_recipes():
    return {"data": mock_database["recipes"], "count": len(mock_database["recipes"])}


# ──────────────────────────────────────────────────────────────
# Agent execution via SSE
# ──────────────────────────────────────────────────────────────

l2_graph = build_l2_graph()
l1_graph = build_graph()

# Track which graph type each thread belongs to (for HITL resume routing)
_thread_graph_type: dict[str, str] = {}  # thread_id -> "l1" | "l2"

class HITLResponse(BaseModel):
    decision: str
    feedback: str = ""

class AgentRequest(BaseModel):
    user_name: str
    user_email: str
    user_query: str
    thread_id: str | None = None
    hitl_response: HITLResponse | None = None


def _serialize_state_delta(delta: dict) -> dict:
    """Convert a LangGraph state delta to a JSON-safe dict."""
    result = {}
    for key, value in delta.items():
        if key == "messages":
            # Serialize LangChain messages
            serialized_msgs = []
            if isinstance(value, list):
                for msg in value:
                    if hasattr(msg, "dict"):
                        msg_dict = msg.dict()
                    elif hasattr(msg, "model_dump"):
                        msg_dict = msg.model_dump()
                    else:
                        msg_dict = {"content": str(msg)}
                    # Extract tool calls if present
                    tool_calls = getattr(msg, "tool_calls", None)
                    if tool_calls:
                        msg_dict["tool_calls"] = [
                            {
                                "name": tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", ""),
                                "args": tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {}),
                            }
                            for tc in tool_calls
                        ]
                    serialized_msgs.append(msg_dict)
            result[key] = serialized_msgs
        else:
            try:
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                result[key] = str(value)
    return result


# ──────────────────────────────────────────────────────────────
# L1 stream helper
# ──────────────────────────────────────────────────────────────

async def _stream_l1(request: AgentRequest, thread_id: str, langfuse_handler, is_resume: bool = False, hitl_response=None):
    """Stream L1 (FAQ) graph execution as SSE events with HITL interrupt support."""
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }

    if is_resume and hitl_response:
        # Same as_node pattern as L2: treat the update as if hitl_node already ran
        if hitl_response.decision == "approve":
            l1_graph.update_state(config, {
                "hitl_decision": "approve",
                "status": "approved",
            }, as_node="hitl_node")
        else:
            feedback_text = hitl_response.feedback or ""
            previous_feedback = l1_graph.get_state(config).values.get("feedback", "")
            if previous_feedback:
                combined = f"{previous_feedback}\n\n[Human Reviewer Feedback]: {feedback_text}"
            else:
                combined = f"[Human Reviewer Feedback]: {feedback_text}"

            l1_graph.update_state(config, {
                "hitl_decision": "request_revision",
                "hitl_feedback": feedback_text,
                "feedback": combined,
                "draft_iterations": 0,
                "status": "in_progress",
            }, as_node="hitl_node")

        resume_json = json.dumps({
            'node_id': '__resume__', 'label': 'Resuming Agent',
            'type': 'system', 'status': 'completed',
            'output': {'thread_id': thread_id},
            'description': 'Resuming after human review.',
        })
        yield f"data: {resume_json}\n\n"
        await asyncio.sleep(0.3)
        input_data = None
    else:
        input_data = {
            "user_query": request.user_query,
            "user_email": request.user_email,
            "user_name": request.user_name,
            "category": "level_1",  # already classified by router
            "retrieved_context": None,
            "retrieval_grade": None,
            "draft_email": None,
            "draft_grade": None,
            "feedback": None,
            "retrieval_iterations": 0,
            "draft_iterations": 0,
            "hitl_decision": None,
            "hitl_feedback": None,
            "status": "in_progress",
        }

    step_count = 0
    try:
        for event in l1_graph.stream(
            input_data,
            config=config,
            stream_mode="updates",
        ):
            if isinstance(event, tuple):
                continue
            for node_id, state_delta in event.items():
                if node_id in ("__interrupt__", "router_node"):
                    continue  # skip router (already ran) and interrupts

                step_count += 1
                meta = NODE_META.get(node_id, {
                    "label": node_id.replace("_", " ").title(),
                    "description": f"Executing {node_id}...",
                    "type": "system",
                })

                if isinstance(state_delta, dict):
                    serialized = _serialize_state_delta(state_delta)
                else:
                    serialized = {"result": str(state_delta)}

                sse_data = {
                    "node_id": node_id,
                    "label": meta["label"],
                    "type": meta["type"],
                    "status": "completed",
                    "description": meta["description"],
                    "output": serialized,
                    "step": step_count,
                }
                yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(1.5)

        # After stream: check if interrupted (HITL) or finished
        state = l1_graph.get_state(config)

        if state.next:
            # Interrupt before hitl_node — send draft for human review
            draft = state.values.get("draft_email")
            interrupt_json = json.dumps({
                'node_id': '__interrupt__',
                'label': 'Awaiting Human Review',
                'type': 'system', 'status': 'paused',
                'output': {'draft_email': draft, 'thread_id': thread_id},
                'description': 'Agent paused for human review.',
            })
            yield f"data: {interrupt_json}\n\n"
        else:
            draft = state.values.get("draft_email")
            end_json = json.dumps({
                'node_id': '__end__',
                'label': 'Agent Complete',
                'type': 'system', 'status': 'completed',
                'output': {'draft_email': draft},
                'description': 'L1 FAQ workflow finished.',
            })
            yield f"data: {end_json}\n\n"

    except Exception as e:
        logger.error("L1 Agent execution error: %s", e, exc_info=True)
        err_json = json.dumps({
            'node_id': '__error__', 'label': 'Error',
            'type': 'system', 'status': 'error',
            'output': {'error': str(e)},
            'description': f'Agent execution failed: {str(e)}',
        })
        yield f"data: {err_json}\n\n"


# ──────────────────────────────────────────────────────────────
# L2 stream helper
# ──────────────────────────────────────────────────────────────

async def _stream_l2(request: AgentRequest, thread_id: str, langfuse_handler, is_resume: bool = False, hitl_response = None):
    """Stream L2 (Data Detective) graph execution as SSE events."""
    import uuid

    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }

    if is_resume and hitl_response:
        if hitl_response.decision == "approve":
            l2_graph.update_state(config, {
                "hitl_decision": "approve",
                "status": "approved",
            }, as_node="l2_hitl_node")
        else:
            feedback_text = hitl_response.feedback or ""
            previous_feedback = l2_graph.get_state(config).values.get("feedback", "")
            if previous_feedback:
                combined = f"{previous_feedback}\n\n[Human Reviewer Feedback]: {feedback_text}"
            else:
                combined = f"[Human Reviewer Feedback]: {feedback_text}"
            
            l2_graph.update_state(config, {
                "hitl_decision": "request_revision",
                "hitl_feedback": feedback_text,
                "feedback": combined,
                "draft_iterations": 0,
                "status": "in_progress",
            }, as_node="l2_hitl_node")
        
        yield f"data: {json.dumps({'node_id': '__resume__', 'label': 'Resuming Agent', 'type': 'system', 'status': 'completed', 'output': {'thread_id': thread_id}, 'description': 'Resuming after human review.'})}\n\n"
        await asyncio.sleep(0.3)
        input_data = None
    else:
        input_data = {
            "user_query": request.user_query,
            "user_email": request.user_email,
            "user_name": request.user_name,
            "restaurant_id": None,
            "messages": [HumanMessage(content=request.user_query)],
            "react_iterations": 0,
            "investigation_context": None,
            "draft_email": None,
            "draft_grade": None,
            "feedback": None,
            "draft_iterations": 0,
            "hitl_decision": None,
            "hitl_feedback": None,
            "status": "in_progress",
        }

    step_count = 0
    final_draft = None
    try:
        for event in l2_graph.stream(
            input_data,
            config=config,
            stream_mode="updates",
        ):
            if isinstance(event, tuple):
                continue
                
            for node_id, state_delta in event.items():
                if node_id == "__interrupt__":
                    continue

                step_count += 1
                if isinstance(state_delta, dict) and "draft_email" in state_delta:
                    final_draft = state_delta["draft_email"]

                meta = NODE_META.get(node_id, {
                    "label": node_id.replace("_", " ").title(),
                    "description": f"Executing {node_id}...",
                    "type": "system",
                })

                if isinstance(state_delta, dict):
                    serialized = _serialize_state_delta(state_delta)
                else:
                    serialized = {"result": str(state_delta)}

                sse_data = {
                    "node_id": node_id,
                    "label": meta["label"],
                    "type": meta["type"],
                    "status": "completed",
                    "description": meta["description"],
                    "output": serialized,
                    "step": step_count,
                }

                yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(1.5)

        # After the stream ends, it's either interrupted or finished
        state = l2_graph.get_state(config)
        
        if state.next:
            draft = state.values.get("draft_email")
            yield f"data: {json.dumps({'node_id': '__interrupt__', 'label': 'Awaiting Human Review', 'type': 'system', 'status': 'paused', 'output': {'draft_email': draft, 'thread_id': thread_id}, 'description': 'Agent paused for human review.'})}\n\n"
        else:
            draft = state.values.get("draft_email")
            yield f"data: {json.dumps({'node_id': '__end__', 'label': 'Agent Complete', 'type': 'system', 'status': 'completed', 'output': {'draft_email': draft}, 'description': 'L2 Data Detective workflow finished.'})}\n\n"

    except Exception as e:
        logger.error("L2 Agent execution error: %s", e, exc_info=True)
        yield f"data: {json.dumps({'node_id': '__error__', 'label': 'Error', 'type': 'system', 'status': 'error', 'output': {'error': str(e)}, 'description': f'Agent execution failed: {str(e)}'})}\n\n"


# ──────────────────────────────────────────────────────────────
# Main stream orchestrator
# ──────────────────────────────────────────────────────────────

async def _stream_agent(request: AgentRequest):
    """
    Main SSE generator:
    1. If resuming (HITL response), dispatch to L1 or L2 based on thread mapping.
    2. Otherwise, run the Router to classify, then dispatch to L1/L2/L3.
    """
    import uuid

    langfuse_handler = get_langfuse_handler()
    thread_id = request.thread_id or str(uuid.uuid4())

    # ── Resume path (HITL) ─────────────────────────────────
    if request.hitl_response:
        graph_type = _thread_graph_type.get(thread_id, "l2")
        logger.info("🔁  Resuming thread %s (graph_type=%s)", thread_id, graph_type)

        if graph_type == "l1":
            async for event in _stream_l1(request, thread_id, langfuse_handler, is_resume=True, hitl_response=request.hitl_response):
                yield event
        else:
            async for event in _stream_l2(request, thread_id, langfuse_handler, is_resume=True, hitl_response=request.hitl_response):
                yield event
        return

    # ── Fresh run: start with Router ───────────────────────
    start_json = json.dumps({
        'node_id': '__start__', 'label': 'Query Received',
        'type': 'system', 'status': 'completed',
        'output': {'user_name': request.user_name, 'user_email': request.user_email, 'user_query': request.user_query, 'thread_id': thread_id},
        'description': 'Customer query received and parsed.',
    })
    yield f"data: {start_json}\n\n"
    await asyncio.sleep(0.5)

    # Run Router classification
    router_result = router_node({"user_query": request.user_query})
    category = router_result.get("category", "level_3")

    router_json = json.dumps({
        'node_id': 'router_node', 'label': 'Query Router',
        'type': 'reasoner', 'status': 'completed',
        'output': {'category': category},
        'description': f'Query classified as {category}.',
        'step': 1,
    })
    yield f"data: {router_json}\n\n"
    await asyncio.sleep(1.0)

    # ── L1: FAQ pipeline ───────────────────────────────────
    if category == "level_1":
        logger.info("🔀  Router → Level 1 (FAQ)")
        _thread_graph_type[thread_id] = "l1"
        async for event in _stream_l1(request, thread_id, langfuse_handler):
            yield event
        return

    # ── L3: Out-of-scope / escalation ──────────────────────
    if category == "level_3":
        logger.info("🔀  Router → Level 3 (Escalation)")
        esc_json = json.dumps({
            'node_id': 'escalate_node', 'label': 'Escalation',
            'type': 'system', 'status': 'completed',
            'output': {'reason': 'Query is out of scope for automated support.'},
            'description': 'Query escalated to human support team.', 'step': 2,
        })
        yield f"data: {esc_json}\n\n"
        await asyncio.sleep(1.0)
        end_json = json.dumps({
            'node_id': '__end__', 'label': 'Agent Complete',
            'type': 'system', 'status': 'completed',
            'output': {'draft_email': None, 'category': 'level_3'},
            'description': 'Query escalated — no automated response.',
        })
        yield f"data: {end_json}\n\n"
        return

    # ── L2: Data Detective ─────────────────────────────────
    logger.info("🔀  Router → Level 2 (Data Detective)")
    _thread_graph_type[thread_id] = "l2"
    async for event in _stream_l2(request, thread_id, langfuse_handler):
        yield event


@app.post("/api/run-agent")
async def run_agent(request: AgentRequest):
    """Stream agent execution as Server-Sent Events."""
    return StreamingResponse(
        _stream_agent(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "haddock-cx-agent"}
