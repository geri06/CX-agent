"""
Haddock CX Agent — Ingest CX Manual into ChromaDB

Reads the CX actuation manual (Markdown), splits it into semantically
meaningful chunks by section headers, and stores them in ChromaDB for
retrieval.

Usage:
    uv run python -m scripts.ingest_manual
"""

import re
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.vectorstore import ingest_chunks, reset_collection  # noqa: E402

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
MANUAL_PATH = PROJECT_ROOT / "data" / "cx_manual.md"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# ──────────────────────────────────────────────────────────────
# Markdown-aware chunking
# ──────────────────────────────────────────────────────────────

def _extract_sections(text: str) -> list[dict]:
    """
    Split the Markdown manual into sections based on ``##`` headers.
    Each section keeps its header as part of the content and records
    the section title as metadata.
    """
    # Split on level-2 headers (## ...)
    pattern = r"(?=^## )"
    raw_sections = re.split(pattern, text, flags=re.MULTILINE)

    sections = []
    for section in raw_sections:
        section = section.strip()
        if not section:
            continue

        # Extract the section title from the first line
        first_line = section.split("\n", 1)[0]
        title = first_line.lstrip("#").strip()

        sections.append({
            "content": section,
            "title": title,
        })

    return sections


def ingest():
    """Read the manual, chunk it, and ingest into ChromaDB."""
    if not MANUAL_PATH.exists():
        print(f"❌  Manual not found at {MANUAL_PATH}")
        sys.exit(1)

    print(f"📖  Reading manual from {MANUAL_PATH}")
    manual_text = MANUAL_PATH.read_text(encoding="utf-8")

    # 1. Split into sections by ## headers
    sections = _extract_sections(manual_text)
    print(f"📑  Found {len(sections)} top-level sections")

    # 2. Further split large sections into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n### ", "\n\n", "\n", ". ", " "],
    )

    all_chunks: list[str] = []
    all_metadatas: list[dict] = []

    for section in sections:
        sub_chunks = splitter.split_text(section["content"])
        for i, chunk in enumerate(sub_chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "section": section["title"],
                "chunk_index": i,
                "source": "cx_manual.md",
            })

    print(f"🔪  Split into {len(all_chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # 3. Reset and re-ingest
    print("🗑️   Resetting existing collection...")
    reset_collection()

    print("📥  Ingesting chunks into ChromaDB...")
    count = ingest_chunks(all_chunks, all_metadatas)

    print(f"\n🎉  Done! {count} chunks ingested into ChromaDB.")
    print(f"    Persistent storage: data/chroma_db/")


if __name__ == "__main__":
    ingest()
