import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  Play,
  UtensilsCrossed,
  FileText,
  Carrot,
  ChefHat,
  ChevronDown,
  Fish,
} from 'lucide-react';

const dataSubItems = [
  { id: 'restaurants', label: 'Restaurants', icon: UtensilsCrossed },
  { id: 'invoices', label: 'Invoices', icon: FileText },
  { id: 'ingredients', label: 'Ingredients', icon: Carrot },
  { id: 'recipes', label: 'Recipes', icon: ChefHat },
];

export default function Sidebar({ activeTab, onTabChange, activeDataSub, onDataSubChange }) {
  const isDataActive = activeTab === 'data';
  const isDemoActive = activeTab === 'demo';

  return (
    <aside className="flex flex-col w-[280px] h-full border border-[var(--color-border)] rounded-2xl bg-[var(--color-bg-surface)] shrink-0 overflow-hidden">
      {/* Logo */}
      <div className="flex items-center gap-3 px-8 py-8 border-b border-[var(--color-border)]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--color-accent)] text-white">
          <Fish size={18} strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--color-text-primary)] tracking-tight">haddock</h1>
          <p className="text-[10px] text-[var(--color-text-tertiary)] font-medium tracking-wider uppercase">CX Agent</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-6 py-8 space-y-2">
        {/* Data Tab */}
        <button
          onClick={() => onTabChange('data')}
          className={`
            flex items-center justify-between w-full px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer
            ${isDataActive
              ? 'bg-[var(--color-accent-glow)] text-[var(--color-accent)] border-l-2 border-[var(--color-accent)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)]'
            }
          `}
        >
          <span className="flex items-center gap-2.5">
            <Database size={16} />
            Data
          </span>
          <motion.div
            animate={{ rotate: isDataActive ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown size={14} className="text-[var(--color-text-tertiary)]" />
          </motion.div>
        </button>

        {/* Data Sub-items */}
        <AnimatePresence>
          {isDataActive && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              <div className="ml-5 pl-4 border-l border-[var(--color-border)] space-y-1 py-2">
                {dataSubItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeDataSub === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onDataSubChange(item.id)}
                      className={`
                        flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-[13px] transition-all duration-150 cursor-pointer
                        ${isActive
                          ? 'text-[var(--color-accent)] bg-[var(--color-accent-glow)] font-medium'
                          : 'text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)]'
                        }
                      `}
                    >
                      <Icon size={14} />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Demo Tab */}
        <button
          onClick={() => onTabChange('demo')}
          className={`
            flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer
            ${isDemoActive
              ? 'bg-[var(--color-accent-glow)] text-[var(--color-accent)] border-l-2 border-[var(--color-accent)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)]'
            }
          `}
        >
          <Play size={16} />
          Demo
        </button>
      </nav>

      {/* Footer */}
      <div className="px-8 py-6 border-t border-[var(--color-border)]">
        <p className="text-[10px] text-[var(--color-text-tertiary)] font-mono">v1.0.0 · L2 Detective</p>
      </div>
    </aside>
  );
}
