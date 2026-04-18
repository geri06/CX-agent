"""
Haddock CX Agent — ChromaDB Vector Store

Provides persistent vector storage and semantic retrieval over the CX
actuation manual.  Uses ChromaDB's built-in default embedding model
(all-MiniLM-L6-v2 via ONNX) so no heavy torch dependency is required.
"""

import logging
import os
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Paths & constants
# ──────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PERSIST_DIR = str(_PROJECT_ROOT / "data" / "chroma_db")
COLLECTION_NAME = "cx_manual"
DEFAULT_N_RESULTS = 4


# ──────────────────────────────────────────────────────────────
# Client & collection helpers
# ──────────────────────────────────────────────────────────────

def _get_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_collection() -> chromadb.Collection:
    """Return (or create) the CX manual collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ──────────────────────────────────────────────────────────────
# Ingestion
# ──────────────────────────────────────────────────────────────

def ingest_chunks(
    chunks: list[str],
    metadatas: list[dict] | None = None,
) -> int:
    """
    Add text chunks to the vector store.

    Parameters
    ----------
    chunks : list[str]
        The text chunks to embed and store.
    metadatas : list[dict], optional
        Per-chunk metadata (e.g. section title, source file).

    Returns
    -------
    int
        Number of chunks ingested.
    """
    collection = get_collection()

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = metadatas or [{}] * len(chunks)

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas,
    )

    logger.info(
        "Ingested %d chunks into collection '%s'",
        len(chunks),
        COLLECTION_NAME,
    )
    return len(chunks)


# ──────────────────────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────────────────────

def retrieve(query: str, n_results: int = DEFAULT_N_RESULTS) -> str:
    """
    Retrieve the most relevant chunks for a given query.

    Parameters
    ----------
    query : str
        The user/rewritten query.
    n_results : int
        Number of chunks to return.

    Returns
    -------
    str
        The concatenated text of the top-k relevant chunks, separated
        by horizontal rules for readability.
    """
    collection = get_collection()

    # Guard: if the collection is empty, return a clear message
    if collection.count() == 0:
        logger.warning("ChromaDB collection '%s' is empty!", COLLECTION_NAME)
        return (
            "[No context available — the knowledge base has not been ingested yet. "
            "Run: uv run python -m scripts.ingest_manual]"
        )

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
    )

    documents = results["documents"][0]

    logger.info(
        "Retrieved %d chunks for query: %s",
        len(documents),
        query[:80],
    )

    return "\n\n---\n\n".join(documents)


def reset_collection() -> None:
    """Delete and recreate the collection (useful for re-ingestion)."""
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted collection '%s'", COLLECTION_NAME)
    except Exception:
        # Collection may not exist yet — that's fine
        pass
    get_collection()
    logger.info("Created fresh collection '%s'", COLLECTION_NAME)
