"""
Haddock CX Agent — Entry Point

Unified entry point for all customer query levels.
ALL queries follow the same input format (user_name, user_email, user_query).

Flow:
    INPUT (name, email, query)
      → L1 GRAPH (router_node classifies into level_1 | level_2 | level_3)
        → level_1: L1 pipeline continues (retrieve → draft → critic → HITL)
        → level_2: L1 graph exits via escalate → main.py dispatches to L2 graph
        → level_3: L1 graph exits via escalate → done (out-of-scope)

The router classification is ALWAYS visible in the Langfuse trace because
it runs inside the graph, not as a separate pre-classification step.

Usage:
    uv run python main.py                     # Interactive scenario picker
    uv run python main.py --s 1               # Scenario 1 (L1 — María)
    uv run python main.py --s 4               # Scenario 4 (L2 — Pepe)
"""

import json
import logging
import sys

from langchain_core.messages import HumanMessage

from src.config import get_langfuse, get_langfuse_handler
from src.graph import build_graph
from src.l2_graph import build_l2_graph

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("haddock-cx-agent")


# ──────────────────────────────────────────────────────────────
# Scenarios — ALL have the same uniform input format
# ──────────────────────────────────────────────────────────────

SCENARIOS = {
    # ── Level 1 (FAQ) ────────────────────────────────────────
    1: {
        "name": "L1 — María password reset",
        "user_name": "María López",
        "user_email": "maria@tabernamaria.es",
        "user_query": (
            "My accountant forgot her password and is locked out. "
            "How do I reset it for her?"
        ),
    },
    2: {
        "name": "L1 — Pepe recipe setup question",
        "user_name": "Pepe García",
        "user_email": "pepe@pizzeriapepe.com",
        "user_query": (
            "How do I create a new escandallo for a recipe in your app? "
            "I can't find the option."
        ),
    },
    # ── Level 3 (Escalation) ────────────────────────────────
    3: {
        "name": "L3 — Nonsensical query",
        "user_name": "Random User",
        "user_email": "random@test.com",
        "user_query": "How can I eat a whole melon with my cat?",
    },
    # ── Level 2 (Data Detective) ────────────────────────────
    4: {
        "name": "L2 — Pepe: Oil typo + bleach",
        "user_name": "Pepe García",
        "user_email": "pepe@pizzeriapepe.com",
        "user_query": (
            "My dashboard says my food cost is at 86.7% which is impossible. "
            "Also, I just checked my 'Hamburguesa Clásica' recipe and the app "
            "says it costs €10.40 to make! I sell it for €12! Your system is "
            "inventing prices. Fix it."
        ),
    },
    5: {
        "name": "L2 — Ana: Low paella cost + conversion rate",
        "user_name": "Ana Martínez",
        "user_email": "ana@elrincondeana.es",
        "user_query": (
            "Something is very wrong with my numbers. My 'Paella Valenciana' "
            "recipe shows it costs €1.90 to make, but the shrimp alone costs "
            "me much more than that. My food cost percentage is at 10.5% which "
            "looks great on paper but I know it's not real. Can you investigate?"
        ),
    },
    6: {
        "name": "L2 — Carlos: Beer miscat + truffle oil",
        "user_name": "Carlos Ruiz",
        "user_email": "carlos@burgerhousecarlos.com",
        "user_query": (
            "My food cost is at 55% which is killing my business. I use "
            "quality ingredients but it shouldn't be that high. Also my "
            "'Smash Burger' recipe cost seems really inflated — the app says "
            "it costs €45 to make a single burger. Something is wrong."
        ),
    },
}


# ──────────────────────────────────────────────────────────────
# L1 results printer
# ──────────────────────────────────────────────────────────────


def _print_l1_results(state: dict) -> None:
    logger.info("═" * 60)
    logger.info("🏁  Level 1 Workflow complete")
    logger.info("─" * 60)
    logger.info("Status           : %s", state.get("status"))
    logger.info("Category         : %s", state.get("category"))
    logger.info("Retrieval iters  : %s", state.get("retrieval_iterations"))
    logger.info("Draft iters      : %s", state.get("draft_iterations"))
    logger.info("Retrieval grade  : %s", state.get("retrieval_grade"))
    logger.info("Draft grade      : %s", state.get("draft_grade"))
    logger.info("─" * 60)
    draft = state.get("draft_email")
    if draft:
        logger.info("📧  Draft email:\n%s", draft)
    else:
        logger.info("📧  No draft email generated (query was escalated).")
    logger.info("═" * 60)


# ──────────────────────────────────────────────────────────────
# L2 results printer
# ──────────────────────────────────────────────────────────────


def _print_l2_results(state: dict) -> None:
    logger.info("═" * 60)
    logger.info("🏁  Level 2 Workflow complete")
    logger.info("─" * 60)
    logger.info("Status               : %s", state.get("status"))
    logger.info("Restaurant ID        : %s", state.get("restaurant_id"))
    logger.info("ReAct iterations     : %s", state.get("react_iterations"))
    logger.info("Draft iterations     : %s", state.get("draft_iterations"))
    logger.info("Draft grade          : %s", state.get("draft_grade"))
    logger.info("─" * 60)
    context = state.get("investigation_context")
    if context:
        logger.info("🔍  Investigation findings:\n%s", context[:500])
    logger.info("─" * 60)
    draft = state.get("draft_email")
    if draft:
        logger.info("📧  Draft email:\n%s", draft)
    else:
        logger.info("📧  No draft email generated.")
    logger.info("═" * 60)


# ──────────────────────────────────────────────────────────────
# Unified entry point
# ──────────────────────────────────────────────────────────────


def run_query(user_name: str, user_email: str, user_query: str) -> dict:
    """
    Unified pipeline:
    1. Always invoke the L1 graph (which includes the router_node).
    2. The router classifies the query (visible in Langfuse trace).
    3. If level_1 → L1 pipeline runs to completion.
    4. If level_2 → L1 graph exits early; we then invoke the L2 graph.
    5. If level_3 → L1 graph exits via escalation.
    """
    langfuse_handler = get_langfuse_handler()

    logger.info("═" * 60)
    logger.info("🐟  Haddock CX Agent — Unified Pipeline")
    logger.info("═" * 60)
    logger.info("👤  Name  : %s", user_name)
    logger.info("📧  Email : %s", user_email)
    logger.info("📨  Query : %s", user_query)
    logger.info("═" * 60)

    # ── Step 1: Invoke L1 graph (router is the first node) ───
    l1_graph = build_graph()

    l1_initial_state = {
        "user_query": user_query,
        "user_email": user_email,
        "user_name": user_name,
        "category": None,  # Router will classify
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

    l1_result = l1_graph.invoke(
        l1_initial_state,
        config={"callbacks": [langfuse_handler]},
    )

    category = l1_result.get("category")
    logger.info("🔀  Router classified query as: %s", category)

    # ── Step 2: If level_1 or level_3, we're done ────────────
    if category == "level_1":
        _print_l1_results(l1_result)
        return l1_result

    if category == "level_3":
        logger.info("🚨  LEVEL 3 — Query escalated (out-of-scope)")
        return l1_result

    # ── Step 3: Level 2 — dispatch to L2 Data Detective ──────
    logger.info("📋  Router classified as LEVEL 2 — dispatching to Data Detective")

    l2_graph = build_l2_graph()

    l2_initial_state = {
        "user_query": user_query,
        "user_email": user_email,
        "user_name": user_name,
        "restaurant_id": None,
        "messages": [HumanMessage(content=user_query)],
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

    l2_result = l2_graph.invoke(
        l2_initial_state,
        config={"callbacks": [langfuse_handler]},
    )

    _print_l2_results(l2_result)
    return l2_result


# ──────────────────────────────────────────────────────────────
# Interactive Scenario Picker
# ──────────────────────────────────────────────────────────────


def interactive_picker() -> None:
    print("\n" + "═" * 60)
    print("  🐟  Haddock CX Agent — Scenario Picker")
    print("═" * 60)
    print()
    for idx, scenario in SCENARIOS.items():
        print(f"    [{idx}]  {scenario['name']}")
    print()
    print("═" * 60)

    choice = input("  Enter scenario number: ").strip()

    try:
        scenario_num = int(choice)
    except ValueError:
        print(f"  ❌  Invalid input: '{choice}'")
        return

    if scenario_num not in SCENARIOS:
        print(f"  ❌  Unknown scenario: {scenario_num}")
        return

    s = SCENARIOS[scenario_num]
    print(f"\n🔍  Running: {s['name']}\n")
    run_and_finish(s)


def run_and_finish(scenario: dict) -> None:
    """Run a scenario through the unified pipeline and flush Langfuse."""
    try:
        final_state = run_query(
            user_name=scenario["user_name"],
            user_email=scenario["user_email"],
            user_query=scenario["user_query"],
        )

        print("\n✅ Final state (JSON):")
        printable = {k: v for k, v in final_state.items() if k != "messages"}
        print(json.dumps(printable, indent=2, ensure_ascii=False))
    finally:
        langfuse = get_langfuse()
        langfuse.flush()
        logger.info("🧹  Langfuse events flushed")


# ──────────────────────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────────────────────


def main():
    """CLI entry point."""
    args = sys.argv[1:]

    # No args → interactive picker
    if not args:
        interactive_picker()
        return

    # Parse --s flag for scenario selection
    if "--s" in args:
        idx = args.index("--s")
        if idx + 1 < len(args):
            scenario_num = int(args[idx + 1])
            if scenario_num not in SCENARIOS:
                logger.error(
                    "Unknown scenario: %d. Available: %s",
                    scenario_num,
                    list(SCENARIOS.keys()),
                )
                return
            s = SCENARIOS[scenario_num]
            print(f"\n🔍  Running: {s['name']}\n")
            run_and_finish(s)
            return

    # Free-text → create an ad-hoc scenario
    query = " ".join(args)
    run_and_finish({
        "user_name": "Test User",
        "user_email": "test@test.com",
        "user_query": query,
    })


if __name__ == "__main__":
    main()
