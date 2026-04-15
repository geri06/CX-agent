export default function StepBullet({
  icon: Icon,
  label,
  description,
  type,
  isActive,
  isPulsing,
  isError,
  isEnd,
  timestamp,
  onClick,
}) {
  const time = timestamp ? new Date(timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }) : '';

  const typeBadge = {
    tool: 'badge-blue',
    reasoner: 'badge-accent',
    system: 'badge-neutral',
  }[type] || 'badge-neutral';

  let bulletColor = 'bg-[var(--color-success)]';
  if (isPulsing) bulletColor = 'bg-[var(--color-accent)]';
  if (isError) bulletColor = 'bg-[var(--color-danger)]';
  if (isEnd) bulletColor = 'bg-[var(--color-success)]';

  return (
    <button
      onClick={onClick}
      className={`
        flex items-start gap-3 w-full text-left py-2 px-2 rounded-lg transition-all duration-150 cursor-pointer group
        ${isActive
          ? 'bg-[var(--color-bg-elevated)] border border-[var(--color-accent)]/30'
          : 'hover:bg-[var(--color-bg-elevated)]/50 border border-transparent'
        }
      `}
    >
      {/* Bullet */}
      <div className="relative mt-0.5 shrink-0">
        <div
          className={`
            w-[18px] h-[18px] rounded-full flex items-center justify-center z-10 relative
            ${isPulsing ? 'pulse-glow' : ''}
            ${bulletColor}
          `}
        >
          <Icon size={10} className="text-white" strokeWidth={2.5} />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[13px] font-medium text-[var(--color-text-primary)] truncate">{label}</span>
          <span className={`badge text-[9px] ${typeBadge}`}>{type}</span>
        </div>
        <p className="text-[11px] text-[var(--color-text-tertiary)] leading-relaxed truncate">
          {description}
        </p>
        {time && (
          <p className="text-[10px] text-[var(--color-text-tertiary)]/50 font-mono mt-0.5">{time}</p>
        )}
      </div>
    </button>
  );
}
