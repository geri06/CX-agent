# 🐟 Haddock CX Agent — Level 1 Queries Workflow

A modular **Corrective RAG (CRAG) / Self-RAG** customer experience agent built with [LangGraph](https://github.com/langchain-ai/langgraph), [ChatGroq](https://console.groq.com/) (Llama 3.3 70B), and [Langfuse](https://langfuse.com/) observability.

## Architecture

```
Customer Query
      │
      ▼
┌─────────────┐
│ Router Node │──── Level 2 ───▶ Escalate Node ──▶ END
└─────┬───────┘
      │ Level 1
      ▼
┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐
│ Retrieve Node│─────▶│ Retrieval Critic │──┬──▶│  Rewrite Query   │─── loop ──┐
│  (ChromaDB)  │      └─────────────────┘  │   └──────────────────┘            │
└──────────────┘            │              │            │                       │
       ▲                    │ relevant     │ irrelevant (max 2 rewrites)        │
       └────────────────────┼──────────────┘                                   │
                            ▼                                                  │
                    ┌──────────────┐      ┌──────────────────────┐             │
                    │  Draft Node  │─────▶│  Generation Critic   │─── fail ───┐│
                    └──────────────┘      └──────────────────────┘            ││
                           ▲                       │                          ││
                           │ feedback loop         │ pass                     ││
                           └───────────────────────┘                          ▼▼
                                                   ▼                  ┌───────────────┐
                                            ┌────────────┐            │ Escalate Node │
                                            │ HITL Node  │            └───────────────┘
                                            └─────┬──────┘
                                                  │
                              ┌────────────────────┼────────────────────┐
                              │                    │                    │
                         Approve             Approve (warn)     Request Revision
                              │                    │                    │
                              ▼                    ▼                    ▼
                             END                  END            Draft Node (reset)
```

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Groq and Langfuse API keys
```

### 3. Ingest the CX manual into ChromaDB

```bash
uv run python -m scripts.ingest_manual
```

This reads `data/cx_manual.md`, chunks it into ~42 sections, embeds them using ChromaDB's built-in ONNX model (all-MiniLM-L6-v2), and stores them in `data/chroma_db/`.

### 4. Seed Langfuse prompts

```bash
uv run python -m scripts.seed_prompts
```

### 5. Run the agent

```bash
# Default Level 1 query
uv run python main.py

# Custom query
uv run python main.py "How do I export guest data from the platform?"

# Test Level 2 escalation
uv run python main.py "I want to dispute the charge on my invoice"
```

## Project Structure

```
haddock-cx-agent/
├── main.py                     # CLI entry point
├── data/
│   ├── cx_manual.md            # CX actuation manual (knowledge base source)
│   └── chroma_db/              # ChromaDB persistent storage (gitignored)
├── src/
│   ├── config.py               # LLM, Langfuse, env vars, iteration limits
│   ├── state.py                # CXAgentState TypedDict
│   ├── prompts.py              # Langfuse prompt fetcher helpers
│   ├── graph.py                # StateGraph assembly + conditional routing
│   ├── nodes/
│   │   ├── router.py           # Classifies query (Level 1 / Level 2)
│   │   ├── retrieve.py         # Fetches context from ChromaDB
│   │   ├── retrieval_critic.py # Grades context relevance
│   │   ├── rewrite_query.py    # Rewrites query for better retrieval
│   │   ├── draft.py            # Drafts CX email response
│   │   ├── generation_critic.py# Evaluates draft quality
│   │   ├── hitl.py             # Human-in-the-loop review (approve / request revision)
│   │   └── escalate.py         # Terminal escalation node
│   └── retrieval/
│       └── vectorstore.py      # ChromaDB vector store (ingest + retrieve)
└── scripts/
    ├── seed_prompts.py         # Seed Langfuse prompts programmatically
    └── ingest_manual.py        # Chunk & ingest CX manual into ChromaDB
```

## Langfuse Prompts

All prompts are managed in Langfuse — **zero hardcoded prompts** in the codebase.

| Prompt Name | Purpose |
|---|---|
| `cx-router` | Classify query as Level 1 or Level 2 |
| `cx-retrieval-critic` | Grade retrieved context relevance |
| `cx-rewrite-query` | Rewrite ambiguous queries |
| `cx-draft-email` | Draft professional CX email |
| `cx-generation-critic` | Evaluate draft against quality rubric |

## Key Design Decisions

- **Real RAG with ChromaDB**: The CX actuation manual is chunked and embedded into a persistent ChromaDB vector store. Retrieval uses semantic similarity search (cosine distance) with the `all-MiniLM-L6-v2` embedding model via ONNX.
- **HITL feedback loop**: The human reviewer can approve the draft or request revisions with feedback. When requesting a revision, the `draft_iterations` counter resets to 0, giving the draft loop a fresh iteration budget.
- **Iteration caps**: Both retrieval (2 rewrites) and drafting (2 re-drafts) loops have strict limits to prevent infinite LLM loops.
- **Defensive parsing**: All LLM output parsers fall back to keyword detection if JSON parsing fails.
- **Separation of concerns**: Each node is a standalone module; routing logic lives in `graph.py`.
- **Observable by default**: Langfuse `CallbackHandler` is injected at graph invocation level, tracing every node.

## Testing the HITL Feedback Loop

To test the revision path, edit `src/nodes/hitl.py` and change:
```python
MOCK_DECISION: str = "approve"
```
to:
```python
MOCK_DECISION: str = "request_revision"
```
This will simulate the human requesting changes, which sends feedback back to the draft node with a fresh iteration budget.
