import { motion } from 'framer-motion';
import { Play, Loader2, CheckCircle2, AlertCircle, User, Mail, MessageSquare, Tag } from 'lucide-react';

function EditableField({ icon: Icon, label, value, onChange, isTextArea = false }) {
  return (
    <div className="flex items-start gap-2 py-2 px-3 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)] focus-within:border-[var(--color-accent)] focus-within:ring-1 focus-within:ring-[var(--color-accent-glow)] transition-all">
      <Icon size={14} className="text-[var(--color-accent-hover)] mt-1 shrink-0" />
      <div className="min-w-0 w-full">
        <label className="text-[10px] text-[var(--color-text-tertiary)] uppercase tracking-wider font-medium block">{label}</label>
        {isTextArea ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full text-[13px] text-[var(--color-text-primary)] mt-0.5 leading-relaxed bg-transparent border-none focus:outline-none resize-none"
            rows={4}
          />
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full text-[13px] text-[var(--color-text-primary)] mt-0.5 leading-relaxed bg-transparent border-none focus:outline-none"
          />
        )}
      </div>
    </div>
  );
}

export default function TicketPanel({ ticket, setTicket, isRunning, isDone, error, onRun }) {
  const updateTicket = (field, value) => {
    setTicket(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="p-8 h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-[var(--color-accent)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-primary)] tracking-tight">Customer Ticket</h2>
        </div>
        <p className="text-xs text-[var(--color-text-tertiary)]">L2 Data Detective Input</p>
      </div>

      {/* Ticket Card */}
      <motion.div
        className="glass-card p-6 space-y-4 flex-1 overflow-y-auto"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <EditableField 
          icon={Tag} 
          label="Scenario" 
          value={ticket.scenarioName} 
          onChange={(v) => updateTicket('scenarioName', v)}
        />
        <EditableField 
          icon={User} 
          label="Customer Name" 
          value={ticket.userName} 
          onChange={(v) => updateTicket('userName', v)}
        />
        <EditableField 
          icon={Mail} 
          label="Email" 
          value={ticket.userEmail} 
          onChange={(v) => updateTicket('userEmail', v)}
        />
        <EditableField 
          icon={MessageSquare} 
          label="Query" 
          value={ticket.userQuery} 
          onChange={(v) => updateTicket('userQuery', v)}
          isTextArea
        />
      </motion.div>

      {/* Run Button */}
      <div className="mt-6 shrink-0">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 p-3 rounded-lg bg-[var(--color-danger-muted)] border border-[var(--color-danger)]/20"
          >
            <div className="flex items-center gap-2">
              <AlertCircle size={14} className="text-[var(--color-danger)]" />
              <p className="text-xs text-[var(--color-danger)]">{error}</p>
            </div>
            <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1 ml-5">
              Ensure the backend is running: <code className="font-mono">uv run uvicorn api_server:app --port 8000</code>
            </p>
          </motion.div>
        )}

        <button
          onClick={onRun}
          disabled={isRunning}
          className={`
            w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
            transition-all duration-200 cursor-pointer
            ${isRunning
              ? 'bg-[var(--color-bg-elevated)] text-[var(--color-text-tertiary)] cursor-not-allowed'
              : isDone
                ? 'bg-[var(--color-success)]/15 text-[var(--color-success)] border border-[var(--color-success)]/30 hover:bg-[var(--color-success)]/25'
                : 'bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] shadow-md shadow-[var(--color-accent)]/20 shadow-sm'
            }
          `}
        >
          {isRunning ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Agent Running...
            </>
          ) : isDone ? (
            <>
              <CheckCircle2 size={16} />
              Run Again
            </>
          ) : (
            <>
              <Play size={16} />
              Run Agent
            </>
          )}
        </button>
      </div>
    </div>
  );
}
