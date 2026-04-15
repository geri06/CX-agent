import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight } from 'lucide-react';

function formatCents(cents) {
  return `€${(cents / 100).toFixed(2)}`;
}

export default function InvoiceTable({ invoices }) {
  const [expandedId, setExpandedId] = useState(null);

  return (
    <div className="glass-card overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider"></th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Invoice ID</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Restaurant</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Supplier</th>
            <th className="text-left px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Date</th>
            <th className="text-right px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Total</th>
            <th className="text-center px-4 py-3 text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => {
            const isExpanded = expandedId === inv.invoice_id;
            return (
              <motion.tr
                key={inv.invoice_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="group"
              >
                <td colSpan={7} className="p-0">
                  <div>
                    {/* Main Row */}
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : inv.invoice_id)}
                      className="flex items-center w-full border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-elevated)]/50 transition-colors cursor-pointer"
                    >
                      <div className="px-4 py-3 w-[40px]">
                        {isExpanded
                          ? <ChevronDown size={14} className="text-[var(--color-text-tertiary)]" />
                          : <ChevronRight size={14} className="text-[var(--color-text-tertiary)]" />
                        }
                      </div>
                      <div className="flex-1 flex items-center">
                        <span className="px-4 py-3 text-xs font-mono text-[var(--color-text-secondary)] w-[140px]">{inv.invoice_id}</span>
                        <span className="px-4 py-3 text-xs font-mono text-[var(--color-text-tertiary)] w-[120px]">{inv.restaurant_id}</span>
                        <span className="px-4 py-3 text-sm text-[var(--color-text-primary)] flex-1">{inv.supplier}</span>
                        <span className="px-4 py-3 text-xs text-[var(--color-text-secondary)] w-[120px]">{inv.issue_date}</span>
                        <span className="px-4 py-3 text-sm font-mono text-[var(--color-text-primary)] text-right w-[100px]">{formatCents(inv.total_amount_cents)}</span>
                        <span className="px-4 py-3 text-center w-[100px]">
                          <span className="badge badge-success">{inv.status}</span>
                        </span>
                      </div>
                    </button>

                    {/* Expanded Line Items */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden bg-[var(--color-bg-elevated)]/30"
                        >
                          <div className="px-8 py-3 ml-10">
                            <p className="text-[10px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider mb-2">Line Items</p>
                            <div className="space-y-2">
                              {inv.line_items.map((item) => (
                                <div key={item.line_id} className="flex items-center justify-between text-xs py-1.5 px-3 rounded-md bg-[var(--color-bg-surface)]">
                                  <div className="flex items-center gap-3">
                                    <span className="font-mono text-[var(--color-text-tertiary)]">{item.line_id}</span>
                                    <span className="text-[var(--color-text-primary)]">{item.raw_text}</span>
                                  </div>
                                  <div className="flex items-center gap-4">
                                    <span className="text-[var(--color-text-tertiary)]">×{item.quantity}</span>
                                    <span className="font-mono text-[var(--color-text-secondary)]">{formatCents(item.unit_price_cents)}</span>
                                    <span className="badge badge-neutral font-mono text-[10px]">{item.mapped_ingredient_id}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
