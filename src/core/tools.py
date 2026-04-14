"""
Haddock CX Agent — Investigation Tools

Native Python tools (``@tool``-decorated) used by the Level 2 ReAct agent
to cross-reference the restaurant's internal data and diagnose
discrepancies (wrong margins, impossible recipe costs, etc.).

All tools return **JSON strings** so the LLM can reliably parse them.
"""

import json
from typing import Optional

from langchain_core.tools import tool

from src.core.mock_db import mock_database


# ──────────────────────────────────────────────────────────────
# Tool 1 — Identity resolution
# ──────────────────────────────────────────────────────────────


@tool
def get_restaurant_id_by_email(email: str) -> str:
    """Look up the restaurant_id and name associated with the given
    email address.  Returns JSON with ``restaurant_id`` and ``name``,
    or an error message if not found."""
    for restaurant in mock_database["restaurants"]:
        if restaurant["email"].lower() == email.lower():
            return json.dumps(
                {
                    "restaurant_id": restaurant["restaurant_id"],
                    "name": restaurant["name"],
                },
                ensure_ascii=False,
            )
    return json.dumps({"error": f"No restaurant found for email: {email}"})


# ──────────────────────────────────────────────────────────────
# Tool 2 — Restaurant profile
# ──────────────────────────────────────────────────────────────


@tool
def get_restaurant_profile(restaurant_id: str) -> str:
    """Retrieve the full profile for a restaurant by its ID, including
    plan, integrations, and the metrics summary (current vs target
    food-cost percentage).  Returns JSON."""
    for restaurant in mock_database["restaurants"]:
        if restaurant["restaurant_id"] == restaurant_id:
            return json.dumps(restaurant, ensure_ascii=False)
    return json.dumps({"error": f"No restaurant found with ID: {restaurant_id}"})


# ──────────────────────────────────────────────────────────────
# Tool 3 — List recipes
# ──────────────────────────────────────────────────────────────


@tool
def list_recipes(restaurant_id: str) -> str:
    """List all recipes registered for a restaurant, including their
    name, sale price, and current recorded cost.  Useful for identifying
    which recipes to audit for cost anomalies.  Returns JSON."""
    results = [
        {
            "recipe_id": r["recipe_id"],
            "name": r["name"],
            "sale_price_cents": r["sale_price_cents"],
            "current_cost_cents": r["current_cost_cents"],
            "margin_pct": round(
                (1 - r["current_cost_cents"] / r["sale_price_cents"]) * 100, 1
            )
            if r["sale_price_cents"] > 0
            else None,
        }
        for r in mock_database["recipes"]
        if r["restaurant_id"] == restaurant_id
    ]

    if not results:
        return json.dumps(
            {"recipes": [], "note": f"No recipes found for {restaurant_id}"}
        )

    return json.dumps(
        {"recipes": results, "count": len(results)}, ensure_ascii=False
    )


# ──────────────────────────────────────────────────────────────
# Tool 4 — Recipe cost audit (escandallo)
# ──────────────────────────────────────────────────────────────


@tool
def audit_recipe_escandallo(restaurant_id: str, recipe_name: str) -> str:
    """Get a specific recipe's escandallo (cost breakdown) for the
    given restaurant.  Cross-references each ingredient's quantity and
    unit against the ingredient catalog and returns a raw data dump.

    The LLM should analyze this raw data to flag anomalies such as:
    - Unit mismatches (e.g. Liters vs Milliliters)
    - Suspiciously high or low quantities
    - Conversion rate errors in the ingredient catalog

    Returns a detailed JSON breakdown."""
    # Find the recipe
    recipe = None
    for r in mock_database["recipes"]:
        if (
            r["restaurant_id"] == restaurant_id
            and r["name"].lower() == recipe_name.lower()
        ):
            recipe = r
            break

    if recipe is None:
        return json.dumps(
            {
                "error": (
                    f"Recipe '{recipe_name}' not found for "
                    f"restaurant {restaurant_id}"
                )
            }
        )

    # Build ingredient lookup
    ingredient_index: dict = {
        ing["ingredient_id"]: ing
        for ing in mock_database["ingredients"]
        if ing["restaurant_id"] == restaurant_id
    }

    audit_lines = []
    total_computed_cost_cents = 0

    for item in recipe["ingredients_used"]:
        ing_id = item["ingredient_id"]
        qty = item["quantity"]
        unit = item["unit"]

        catalog_entry = ingredient_index.get(ing_id)

        if catalog_entry:
            cost = qty * catalog_entry["average_cost_per_recipe_unit_cents"]
            total_computed_cost_cents += cost

            audit_lines.append(
                {
                    "ingredient_id": ing_id,
                    "name": catalog_entry["name"],
                    "quantity_in_recipe": qty,
                    "unit_in_recipe": unit,
                    "catalog_recipe_unit": catalog_entry["recipe_unit"],
                    "catalog_purchase_unit": catalog_entry["purchase_unit"],
                    "catalog_conversion_rate": catalog_entry["conversion_rate"],
                    "computed_cost_cents": cost,
                }
            )
        else:
            audit_lines.append(
                {
                    "ingredient_id": ing_id,
                    "quantity_in_recipe": qty,
                    "unit_in_recipe": unit,
                    "catalog_error": "N/A (not in catalog)",
                    "computed_cost_cents": "unknown",
                }
            )

    result = {
        "recipe_name": recipe["name"],
        "recipe_id": recipe["recipe_id"],
        "sale_price_cents": recipe["sale_price_cents"],
        "recorded_cost_cents": recipe["current_cost_cents"],
        "computed_cost_cents": total_computed_cost_cents,
        "line_items_audit": audit_lines,
    }
    return json.dumps(result, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# Tool 5 — Ingredient catalog browser
# ──────────────────────────────────────────────────────────────


@tool
def get_ingredient_catalog(
    restaurant_id: str, category: Optional[str] = None
) -> str:
    """List all ingredients for a restaurant, optionally filtered by
    category (e.g. 'food', 'cleaning', 'beverage').  Useful for
    spotting miscategorised items (like cleaning products filed under
    'food', or beverages filed as 'food') that inflate the restaurant's
    food-cost percentage.  Returns JSON."""
    results = [
        ing
        for ing in mock_database["ingredients"]
        if ing["restaurant_id"] == restaurant_id
        and (category is None or ing["category"].lower() == category.lower())
    ]

    if not results:
        msg = f"No ingredients found for restaurant {restaurant_id}"
        if category:
            msg += f" in category '{category}'"
        return json.dumps({"ingredients": [], "note": msg})

    return json.dumps(
        {"ingredients": results, "count": len(results)}, ensure_ascii=False
    )


# ──────────────────────────────────────────────────────────────
# Tool registry (for the tool executor node)
# ──────────────────────────────────────────────────────────────

INVESTIGATION_TOOLS = [
    get_restaurant_id_by_email,
    get_restaurant_profile,
    list_recipes,
    audit_recipe_escandallo,
    get_ingredient_catalog,
]

TOOL_REGISTRY: dict = {t.name: t for t in INVESTIGATION_TOOLS}
