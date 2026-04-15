import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

function formatCents(cents) {
  return `€${(cents / 100).toFixed(2)}`;
}

export default function RecipeCard({ recipe }) {
  const { name, recipe_id, restaurant_id, sale_price_cents, current_cost_cents, ingredients_used } = recipe;
  const margin = sale_price_cents > 0
    ? ((1 - current_cost_cents / sale_price_cents) * 100).toFixed(1)
    : 0;
  const isNegativeMargin = parseFloat(margin) < 0;
  const isLowMargin = parseFloat(margin) < 30 && !isNegativeMargin;

  return (
    <div className="glass-card-hoverable p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{name}</h3>
          <p className="text-xs text-[var(--color-text-tertiary)] font-mono mt-0.5">{recipe_id} · {restaurant_id}</p>
        </div>
        <div className={`flex items-center gap-1 badge ${isNegativeMargin ? 'badge-danger' : isLowMargin ? 'badge-warning' : 'badge-success'}`}>
          {isNegativeMargin ? <TrendingDown size={12} /> : <TrendingUp size={12} />}
          {margin}%
        </div>
      </div>

      {/* Price row */}
      <div className="flex items-center gap-4 mb-4">
        <div>
          <p className="text-[10px] text-[var(--color-text-tertiary)] uppercase tracking-wider mb-0.5">Sale Price</p>
          <p className="text-lg font-semibold font-mono text-[var(--color-text-primary)]">
            {formatCents(sale_price_cents)}
          </p>
        </div>
        <div className="w-px h-8 bg-[var(--color-border)]" />
        <div>
          <p className="text-[10px] text-[var(--color-text-tertiary)] uppercase tracking-wider mb-0.5">Cost</p>
          <p className={`text-lg font-semibold font-mono ${isNegativeMargin ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-primary)]'}`}>
            {formatCents(current_cost_cents)}
          </p>
        </div>
        {isNegativeMargin && (
          <div className="ml-auto">
            <AlertTriangle size={18} className="text-[var(--color-danger)]" />
          </div>
        )}
      </div>

      {/* Ingredients breakdown */}
      <div>
        <p className="text-[10px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider mb-2">Ingredients</p>
        <div className="space-y-1.5">
          {ingredients_used.map((ing, i) => (
            <div key={i} className="flex items-center justify-between text-xs py-1.5 px-3 rounded-md bg-[var(--color-bg-elevated)]">
              <span className="font-mono text-[var(--color-accent-hover)]">{ing.ingredient_id}</span>
              <span className="text-[var(--color-text-secondary)]">
                {ing.quantity} <span className="text-[var(--color-text-tertiary)]">{ing.unit}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
