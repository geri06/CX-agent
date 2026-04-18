"""
Haddock CX Agent — Feedback Logger

Appends human HITL feedback from Level 1 queries to the CX manual
(cx_manualv1.md) and triggers a full re-ingestion into ChromaDB so
future retrievals benefit from accumulated human corrections.

Usage (called from api_server.py during L1 HITL revision):
    from src.utils.feedback_logger import append_feedback_to_manual
    append_feedback_to_manual(user_query, human_feedback)
"""

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANUAL_PATH = _PROJECT_ROOT / "data" / "cx_manualv1.md"

# Section header that we append feedback under
_SECTION_HEADER = "## CX Human Feedback"


def append_feedback_to_manual(user_query: str, human_feedback: str) -> None:
    """
    Append a timestamped human-feedback entry to ``cx_manualv1.md``
    and re-ingest the manual into ChromaDB.

    Parameters
    ----------
    user_query : str
        The original customer query that triggered the draft.
    human_feedback : str
        The free-text feedback provided by the human reviewer.
    """
    if not human_feedback or not human_feedback.strip():
        logger.info("⏭️  Feedback logger — empty feedback, skipping.")
        return

    # ── Build the new entry ──────────────────────────────────
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n### Feedback — {timestamp}\n"
        f"- **Original Query:** \"{user_query}\"\n"
        f"- **Human Feedback:** \"{human_feedback}\"\n"
    )

    # ── Read / update the manual ─────────────────────────────
    if not MANUAL_PATH.exists():
        logger.error("❌  Manual not found at %s — cannot append feedback.", MANUAL_PATH)
        return

    manual_text = MANUAL_PATH.read_text(encoding="utf-8")

    if _SECTION_HEADER in manual_text:
        # Section exists → append entry at the very end of the file
        # (the section is always the last one, so appending to EOF works)
        updated_text = manual_text.rstrip() + "\n" + entry
    else:
        # Section does not exist → create it at the end
        updated_text = (
            manual_text.rstrip()
            + "\n\n-----\n\n"
            + _SECTION_HEADER
            + "\n"
            + entry
        )

    MANUAL_PATH.write_text(updated_text, encoding="utf-8")
    logger.info(
        "📝  Feedback logger — appended entry to %s (query: %s…)",
        MANUAL_PATH.name,
        user_query[:60],
    )

    # ── Re-ingest into ChromaDB (blocking) ───────────────────
    try:
        import sys
        import io
        from scripts.ingest_manual import ingest

        # The ingest script uses emoji in print() which can fail on
        # Windows consoles with cp1252 encoding.  Temporarily redirect
        # stdout to a UTF-8 capable stream.
        original_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        try:
            ingest()
        finally:
            sys.stdout = original_stdout

        logger.info("Feedback logger — ChromaDB re-ingestion complete.")
    except Exception:
        logger.exception("Feedback logger — ChromaDB re-ingestion failed.")
