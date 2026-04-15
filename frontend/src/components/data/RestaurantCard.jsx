import { Activity, Plug, Crown } from 'lucide-react';

function FoodCostGauge({ current, target }) {
  const isOver = current > target;
  const ratio = Math.min(current / 100, 1);
  const barColor = isOver ? 'var(--color-danger)' : 'var(--color-success)';
  const targetPos = `${target}%`;

  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] text-[var(--color-text-tertiary)] font-medium uppercase tracking-wider">Food Cost</span>
        <span className={`text-sm font-semibold font-mono ${isOver ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'}`}>
          {current}%
        </span>
      </div>
      <div className="relative h-2 bg-[var(--color-bg-elevated)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${ratio * 100}%`, background: barColor }}
        />
        {/* Target marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-[var(--color-text-tertiary)]"
          style={{ left: targetPos }}
          title={`Target: ${target}%`}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-[var(--color-text-tertiary)]">0%</span>
        <span className="text-[10px] text-[var(--color-text-tertiary)]">Target: {target}%</span>
      </div>
    </div>
  );
}

export default function RestaurantCard({ restaurant }) {
  const { name, restaurant_id, email, plan, status, integrations, metrics_summary } = restaurant;

  const planBadge = plan === 'Pro' ? 'badge-accent' : 'badge-neutral';

  return (
    <div className="glass-card-hoverable p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{name}</h3>
          <p className="text-xs text-[var(--color-text-tertiary)] font-mono mt-0.5">{restaurant_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${planBadge}`}>
            <Crown size={10} />
            {plan}
          </span>
          <span className={`badge ${status === 'Active' ? 'badge-success' : 'badge-danger'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${status === 'Active' ? 'bg-[var(--color-success)]' : 'bg-[var(--color-danger)]'}`} />
            {status}
          </span>
        </div>
      </div>

      {/* Email */}
      <p className="text-xs text-[var(--color-text-secondary)] mb-3">{email}</p>

      {/* Integrations */}
      <div className="flex items-center gap-2 mb-3">
        <Plug size={12} className="text-[var(--color-text-tertiary)]" />
        {integrations.pos && <span className="badge badge-blue">{integrations.pos}</span>}
        {integrations.accounting && <span className="badge badge-neutral">{integrations.accounting}</span>}
        {!integrations.accounting && <span className="badge badge-warning">No accounting</span>}
      </div>

      {/* Food Cost Gauge */}
      <FoodCostGauge
        current={metrics_summary.current_food_cost_pct}
        target={metrics_summary.target_food_cost_pct}
      />
    </div>
  );
}
