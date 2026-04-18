"""
Haddock CX Agent — Mock Database

Simulates the internal haddock platform database for the Level 2
"Data Detective" workflow.  Contains restaurants, invoices, ingredients,
and recipes with deliberately planted data-entry errors for testing.

═══════════════════════════════════════════════════════════════
Scenario 1 — "La Pizzería de Pepe" (rest_102)
───────────────────────────────────────────────────────────────
  Customer complaint : Food cost 45.2% (target 28%), burger costs €150.
  Planted errors:
    1. Recipe "Hamburguesa Clásica" → oil listed as 1 Liter (should be mL).
    2. Ingredient "Lejía Conejo" (bleach) miscategorised as "food".

═══════════════════════════════════════════════════════════════
Scenario 2 — "El Rincón de Ana" (rest_205)
───────────────────────────────────────────────────────────────
  Customer complaint : Paella recipe shows €3.50 cost, but ingredients
                       alone should be ≈€12.  Margins look suspiciously good.
  Planted errors:
    1. Saffron quantity in recipe: 0.5 g instead of 5 g (10× under-count).
    2. Shrimp ingredient has conversion_rate = 1 instead of 1000
       (purchase_unit=KG, recipe_unit=Grams), so the per-gram cost
       is 1000× too high — but it "cancels out" with the wrong quantity,
       making the final cost look low.  The agent must flag the
       conversion_rate as the root issue.

═══════════════════════════════════════════════════════════════
Scenario 3 — "Burger House Carlos" (rest_310)
───────────────────────────────────────────────────────────────
  Customer complaint : Food cost 55%, unsustainable.  Smash Burger
                       recipe cost seems fine individually.
  Planted errors:
    1. "Cerveza Artesana Premium" (craft beer) miscategorised as "food"
       instead of "beverage", inflating the food-cost percentage.
    2. Recipe "Smash Burger" lists 500 mL of truffle oil for a single
       burger (should be 5 mL — 100× over-count).
═══════════════════════════════════════════════════════════════
Scenario 7 — "Pescados de Laura" (rest_400)
───────────────────────────────────────────────────────────────
  Customer complaint : "My Salmón al Horno is showing a food cost of 80%!"
  Planted errors:
    NONE. The data is entirely correct. The salmon is simply very expensive
    and she is selling it too cheap.
    EXPECTED OUTCOME: Agent should fail to find a data bug and Escalate.
═══════════════════════════════════════════════════════════════
"""

mock_database: dict = {
    # ──────────────────────────────────────────────────────
    # RESTAURANTS
    # ──────────────────────────────────────────────────────
    "restaurants": [
        # ── Scenario 1 ─────────────────────────────────────
        {
            "restaurant_id": "rest_102",
            "email": "pepe@pizzeriapepe.com",
            "name": "La Pizzería de Pepe",
            "plan": "Pro",
            "status": "Active",
            "integrations": {"pos": "Square", "accounting": "Holded"},
            "metrics_summary": {
                "current_food_cost_pct": 86.7,
                "target_food_cost_pct": 28.0,
            },
        },
        # ── Scenario 2 ─────────────────────────────────────
        {
            "restaurant_id": "rest_205",
            "email": "ana@elrincondeana.es",
            "name": "El Rincón de Ana",
            "plan": "Pro",
            "status": "Active",
            "integrations": {"pos": "Lightspeed", "accounting": "Contasol"},
            "metrics_summary": {
                "current_food_cost_pct": 10.5,
                "target_food_cost_pct": 30.0,
            },
        },
        # ── Scenario 3 ─────────────────────────────────────
        {
            "restaurant_id": "rest_310",
            "email": "carlos@burgerhousecarlos.com",
            "name": "Burger House Carlos",
            "plan": "Starter",
            "status": "Active",
            "integrations": {"pos": "Glovo POS", "accounting": None},
            "metrics_summary": {
                "current_food_cost_pct": 55.0,
                "target_food_cost_pct": 30.0,
            },
        },
        # ── Scenario 7 (Escalation) ────────────────────────
        {
            "restaurant_id": "rest_400",
            "email": "laura@pescadosdelaura.com",
            "name": "Pescados de Laura",
            "plan": "Pro",
            "status": "Active",
            "integrations": {"pos": "Square", "accounting": "Holded"},
            "metrics_summary": {
                "current_food_cost_pct": 80.0,
                "target_food_cost_pct": 30.0,
            },
        },
        # ── L1 FAQ test customer ────────────────────────────
        {
            "restaurant_id": "rest_401",
            "email": "maria@tabernamaria.es",
            "name": "La Taberna de María",
            "plan": "Starter",
            "status": "Active",
            "integrations": {"pos": "Revel", "accounting": "Holded"},
            "metrics_summary": {
                "current_food_cost_pct": 29.0,
                "target_food_cost_pct": 30.0,
            },
        },
    ],

    # ──────────────────────────────────────────────────────
    # INVOICES
    # ──────────────────────────────────────────────────────
    "invoices": [
        # ── Pepe ────────────────────────────────────────────
        {
            "invoice_id": "inv_88392",
            "restaurant_id": "rest_102",
            "document_type": "invoice",
            "supplier": "Distribuciones Makro",
            "issue_date": "2026-04-10",
            "total_amount_cents": 45050,
            "status": "processed",
            "line_items": [
                {
                    "line_id": "line_1",
                    "raw_text": "TOMATE FRITO LATA 5KG",
                    "quantity": 2,
                    "unit_price_cents": 1250,
                    "mapped_ingredient_id": "ing_tom_01",
                },
                {
                    "line_id": "line_2",
                    "raw_text": "LEJIA CONEJO 5L",
                    "quantity": 1,
                    "unit_price_cents": 500,
                    "mapped_ingredient_id": "ing_lej_02",
                },
            ],
        },
        # ── Ana ─────────────────────────────────────────────
        {
            "invoice_id": "inv_90210",
            "restaurant_id": "rest_205",
            "document_type": "invoice",
            "supplier": "Mariscos del Mediterráneo",
            "issue_date": "2026-04-08",
            "total_amount_cents": 128000,
            "status": "processed",
            "line_items": [
                {
                    "line_id": "line_1",
                    "raw_text": "GAMBA ROJA FRESCA 2KG",
                    "quantity": 2,
                    "unit_price_cents": 10000,
                    "mapped_ingredient_id": "ing_gamba_01",
                },
                {
                    "line_id": "line_2",
                    "raw_text": "AZAFRAN MANCHA 10G",
                    "quantity": 1,
                    "unit_price_cents": 200,
                    "mapped_ingredient_id": "ing_azafran_01",
                },
            ],
        },
        # ── Carlos ──────────────────────────────────────────
        {
            "invoice_id": "inv_77501",
            "restaurant_id": "rest_310",
            "document_type": "invoice",
            "supplier": "Bebidas Premium S.L.",
            "issue_date": "2026-04-09",
            "total_amount_cents": 96000,
            "status": "processed",
            "line_items": [
                {
                    "line_id": "line_1",
                    "raw_text": "CERVEZA ARTESANA CRAFT IPA 24x33cl",
                    "quantity": 4,
                    "unit_price_cents": 24000,
                    "mapped_ingredient_id": "ing_cerveza_01",
                },
            ],
        },
        {
            "invoice_id": "inv_77502",
            "restaurant_id": "rest_310",
            "document_type": "invoice",
            "supplier": "Congelados y Salsas S.A.",
            "issue_date": "2026-04-10",
            "total_amount_cents": 13000,
            "status": "processed",
            "line_items": [
                {
                    "line_id": "line_1",
                    "raw_text": "TEQUEÑOS DE QUESO CAJA 50U",
                    "quantity": 2,
                    "unit_price_cents": 2500,
                    "mapped_ingredient_id": "ing_tequeno_01",
                },
                {
                    "line_id": "line_2",
                    "raw_text": "SALSA DE AJO 5L",
                    "quantity": 1,
                    "unit_price_cents": 8000,
                    "mapped_ingredient_id": "ing_salsa_ajo_01",
                },
            ],
        },
        # ── Laura ───────────────────────────────────────────
        {
            "invoice_id": "inv_40011",
            "restaurant_id": "rest_400",
            "document_type": "invoice",
            "supplier": "Pescados del Norte",
            "issue_date": "2026-04-12",
            "total_amount_cents": 50000,
            "status": "processed",
            "line_items": [
                {
                    "line_id": "line_1",
                    "raw_text": "SALMON NORUEGO ENTERO 20KG",
                    "quantity": 1,
                    "unit_price_cents": 50000,
                    "mapped_ingredient_id": "ing_salmon_01",
                },
            ],
        },
    ],

    # ──────────────────────────────────────────────────────
    # INGREDIENTS
    # ──────────────────────────────────────────────────────
    "ingredients": [
        # ── Pepe (rest_102) ─────────────────────────────────
        {
            "ingredient_id": "ing_lej_02",
            "restaurant_id": "rest_102",
            "name": "Lejía Conejo",
            "category": "food",  # ← BUG: should be "cleaning"
            "purchase_unit": "Liters",
            "recipe_unit": "Milliliters",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 0.5,
        },
        {
            "ingredient_id": "ing_aceite_01",
            "restaurant_id": "rest_102",
            "name": "Aceite de Oliva Virgen Extra",
            "category": "food",
            "purchase_unit": "Liters",
            "recipe_unit": "Milliliters",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 0.8,
        },
        {
            "ingredient_id": "ing_carne_01",
            "restaurant_id": "rest_102",
            "name": "Carne Picada Ternera",
            "category": "food",
            "purchase_unit": "Kilograms",
            "recipe_unit": "Grams",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 1.2,
        },

        # ── Ana (rest_205) ──────────────────────────────────
        {
            "ingredient_id": "ing_gamba_01",
            "restaurant_id": "rest_205",
            "name": "Gamba Roja Fresca",
            "category": "food",
            "purchase_unit": "Kilograms",
            "recipe_unit": "Grams",
            "conversion_rate": 1,  # ← BUG: should be 1000 (KG→Grams)
            "average_cost_per_recipe_unit_cents": 5.0,
        },
        {
            "ingredient_id": "ing_azafran_01",
            "restaurant_id": "rest_205",
            "name": "Azafrán de la Mancha",
            "category": "food",
            "purchase_unit": "Grams",
            "recipe_unit": "Grams",
            "conversion_rate": 1,
            "average_cost_per_recipe_unit_cents": 20.0,
        },
        {
            "ingredient_id": "ing_arroz_01",
            "restaurant_id": "rest_205",
            "name": "Arroz Bomba",
            "category": "food",
            "purchase_unit": "Kilograms",
            "recipe_unit": "Grams",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 0.3,
        },

        # ── Carlos (rest_310) ───────────────────────────────
        # {
        #     "ingredient_id": "ing_cerveza_01",
        #     "restaurant_id": "rest_310",
        #     "name": "Cerveza Artesana Premium",
        #     "category": "food",  # ← BUG: should be "beverage"
        #     "purchase_unit": "Units",
        #     "recipe_unit": "Units",
        #     "conversion_rate": 1,
        #     "average_cost_per_recipe_unit_cents": 250.0,
        # },
        {
            "ingredient_id": "ing_truffle_oil_01",
            "restaurant_id": "rest_310",
            "name": "Aceite de Trufa Negra",
            "category": "food",
            "purchase_unit": "Liters",
            "recipe_unit": "Milliliters",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 8.5,
        },
        {
            "ingredient_id": "ing_carne_smash_01",
            "restaurant_id": "rest_310",
            "name": "Blend Smash Burger (wagyu mix)",
            "category": "food",
            "purchase_unit": "Kilograms",
            "recipe_unit": "Grams",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 2.5,
        },
        {
            "ingredient_id": "ing_pan_brioche_01",
            "restaurant_id": "rest_310",
            "name": "Pan Brioche",
            "category": "food",
            "purchase_unit": "Units",
            "recipe_unit": "Units",
            "conversion_rate": 1,
            "average_cost_per_recipe_unit_cents": 35.0,
        },
        {
            "ingredient_id": "ing_tequeno_01",
            "restaurant_id": "rest_310",
            "name": "Tequeños de Queso",
            "category": "food",
            "purchase_unit": "Units",
            "recipe_unit": "Units",
            "conversion_rate": 1,
            "average_cost_per_recipe_unit_cents": 50.0,
        },
        {
            "ingredient_id": "ing_salsa_ajo_01",
            "restaurant_id": "rest_310",
            "name": "Salsa de Ajo",
            "category": "food",
            "purchase_unit": "Liters",
            "recipe_unit": "Milliliters",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 1.6,
        },

        # ── Laura (rest_400) ────────────────────────────────
        {
            "ingredient_id": "ing_salmon_01",
            "restaurant_id": "rest_400",
            "name": "Salmón Noruego Entero",
            "category": "food",
            "purchase_unit": "Kilograms",
            "recipe_unit": "Grams",
            "conversion_rate": 1000,
            "average_cost_per_recipe_unit_cents": 2.5,  # 25€/KG is correct
        },
    ],

    # ──────────────────────────────────────────────────────
    # RECIPES
    # ──────────────────────────────────────────────────────
    "recipes": [
        # ── Pepe (rest_102) ─────────────────────────────────
        {
            "recipe_id": "rec_burger_01",
            "restaurant_id": "rest_102",
            "name": "Hamburguesa Clásica",
            "sale_price_cents": 1200,
            "current_cost_cents": 1040,  # inflated because of oil typo
            "ingredients_used": [
                {"ingredient_id": "ing_carne_01", "quantity": 200, "unit": "Grams"},
                {"ingredient_id": "ing_aceite_01", "quantity": 1, "unit": "Liters"},  # ← BUG: should be mL
            ],
        },

        # ── Ana (rest_205) ──────────────────────────────────
        {
            "recipe_id": "rec_paella_01",
            "restaurant_id": "rest_205",
            "name": "Paella Valenciana",
            "sale_price_cents": 1800,
            "current_cost_cents": 190,  # suspiciously low
            "ingredients_used": [
                {"ingredient_id": "ing_arroz_01", "quantity": 300, "unit": "Grams"},
                {"ingredient_id": "ing_gamba_01", "quantity": 100, "unit": "Grams"},
                {"ingredient_id": "ing_azafran_01", "quantity": 5, "unit": "Grams"},  # ← BUG: should be 5g
            ],
        },

        # ── Carlos (rest_310) ───────────────────────────────
        {
            "recipe_id": "rec_smash_01",
            "restaurant_id": "rest_310",
            "name": "Smash Burger",
            "sale_price_cents": 1450,
            "current_cost_cents": 4535,  # inflated because of truffle oil typo
            "ingredients_used": [
                {"ingredient_id": "ing_carne_smash_01", "quantity": 150, "unit": "Grams"},
                {"ingredient_id": "ing_pan_brioche_01", "quantity": 1, "unit": "Units"},
                {"ingredient_id": "ing_truffle_oil_01", "quantity": 500, "unit": "Milliliters"},  # ← BUG: should be 5 mL
            ],
        },
        {
            "recipe_id": "rec_tequeno_01",
            "restaurant_id": "rest_310",
            "name": "Ración de Tequeños",
            "sale_price_cents": 850,
            "current_cost_cents": 348,
            "ingredients_used": [
                {"ingredient_id": "ing_tequeno_01", "quantity": 6, "unit": "Units"},
                {"ingredient_id": "ing_salsa_ajo_01", "quantity": 30, "unit": "Milliliters"},
            ],
        },

        # ── Laura (rest_400) - PERFECT DATA, HIGH COST ──────
        {
            "recipe_id": "rec_salmon_01",
            "restaurant_id": "rest_400",
            "name": "Salmón al Horno",
            "sale_price_cents": 625,   # €6.25 (Very cheap for salmon!)
            "current_cost_cents": 500, # €5.00 (200g * 2.5 cents/g)
            "ingredients_used": [
                {"ingredient_id": "ing_salmon_01", "quantity": 200, "unit": "Grams"},
            ],
        },
    ],
}
