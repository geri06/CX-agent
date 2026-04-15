import { motion } from 'framer-motion';

const CATEGORY_BADGES = {
  food: 'badge-success',
  cleaning: 'badge-warning',
  beverage: 'badge-blue',
};

export default function IngredientTable({ ingredients }) {
  return (
    <div className="glass-card overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Name</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">ID</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Restaurant</th>
            <th className="text-center px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Category</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Purchase → Recipe</th>
            <th className="text-right px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Conv. Rate</th>
            <th className="text-right px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Cost/Unit (¢)</th>
          </tr>
        </thead>
        <tbody>
          {ingredients.map((ing, i) => {
            const badgeClass = CATEGORY_BADGES[ing.category] || 'badge-neutral';
            return (
              <motion.tr
                key={ing.ingredient_id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-elevated)]/30 transition-colors"
              >
                <td className="px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium">{ing.name}</td>
                <td className="px-4 py-3 text-xs font-mono text-[var(--color-text-tertiary)]">{ing.ingredient_id}</td>
                <td className="px-4 py-3 text-xs font-mono text-[var(--color-text-tertiary)]">{ing.restaurant_id}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`badge ${badgeClass}`}>{ing.category}</span>
                </td>
                <td className="px-4 py-3 text-xs text-[var(--color-text-secondary)]">
                  <span className="font-mono">{ing.purchase_unit}</span>
                  <span className="text-[var(--color-text-tertiary)] mx-1">→</span>
                  <span className="font-mono">{ing.recipe_unit}</span>
                </td>
                <td className="px-4 py-3 text-sm font-mono text-right text-[var(--color-text-primary)]">
                  {ing.conversion_rate.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm font-mono text-right text-[var(--color-text-primary)]">
                  {ing.average_cost_per_recipe_unit_cents}
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
