import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import StepBullet from './StepBullet';
import {
  Radio,
  GitBranch,
  Wrench,
  Brain,
  FileText,
  ShieldCheck,
  UserCheck,
  AlertTriangle,
  Play,
  CheckCircle2,
  Search,
  Filter,
  PenLine,
  RotateCcw,
} from 'lucide-react';

const NODE_ICONS = {
  '__start__': Play,
  // Router
  'router_node': Filter,
  // L1 nodes
  'retrieve_node': Search,
  'retrieval_critic_node': ShieldCheck,
  'rewrite_query_node': RotateCcw,
  'draft_node': PenLine,
  'generation_critic_node': ShieldCheck,
  'hitl_node': UserCheck,
  'escalate_node': AlertTriangle,
  // L2 nodes
  'identity_node': Radio,
  'reasoner_node': Brain,
  'tool_executor_node': Wrench,
  'extract_findings_node': FileText,
  'l2_draft_node': PenLine,
  'l2_critic_node': ShieldCheck,
  'l2_hitl_node': UserCheck,
  'l2_escalate_node': AlertTriangle,
  // Terminal
  '__end__': CheckCircle2,
  '__error__': AlertTriangle,
};

function getStepIcon(nodeId) {
  return NODE_ICONS[nodeId] || GitBranch;
}

export default function TracePanel({ steps, activeNodeId, isRunning, onStepClick }) {
  const bottomRef = useRef(null);

  // Auto-scroll to the latest step
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps.length]);

  return (
    <div className="p-8 h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-[var(--color-accent)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-primary)] tracking-tight">Agent Trace</h2>
        </div>
        <p className="text-xs text-[var(--color-text-tertiary)]">
          LangGraph node execution · {steps.length} step{steps.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Steps */}
      <div className="flex-1 overflow-y-auto pr-1">
        {steps.length === 0 && !isRunning && (
          <div className="flex items-center justify-center h-48 text-center">
            <div>
              <GitBranch size={28} className="mx-auto mb-2 text-[var(--color-text-tertiary)]/40" />
              <p className="text-sm text-[var(--color-text-tertiary)]">No trace yet</p>
              <p className="text-xs text-[var(--color-text-tertiary)]/60 mt-1">Click "Run Agent" to start</p>
            </div>
          </div>
        )}

        <div className="relative">
          {/* Vertical connecting line */}
          {steps.length > 0 && (
            <div
              className="absolute left-[15px] top-[20px] w-[2px] bg-[var(--color-border)]"
              style={{ height: `calc(100% - 40px)` }}
            />
          )}

          {/* Step items */}
          <div className="space-y-1">
            {steps.map((step, index) => {
              const Icon = getStepIcon(step.nodeId);
              const isActive = step.id === activeNodeId;
              const isLast = index === steps.length - 1;
              const isTerminal = step.nodeId === '__end__' || step.nodeId === '__error__';

              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.25, delay: 0.05 }}
                >
                  <StepBullet
                    icon={Icon}
                    label={step.label}
                    description={step.description}
                    type={step.type}
                    isActive={isActive}
                    isPulsing={isLast && isRunning && !isTerminal}
                    isError={step.nodeId === '__error__'}
                    isEnd={step.nodeId === '__end__'}
                    timestamp={step.timestamp}
                    onClick={() => onStepClick(step.id)}
                  />
                </motion.div>
              );
            })}
          </div>

          {/* Pulsing dot for "thinking" at the bottom when running */}
          {isRunning && (
            <motion.div
              className="flex items-center gap-3 py-2 pl-[7px] mt-1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="w-[18px] h-[18px] rounded-full flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-[var(--color-accent)] pulse-glow" />
              </div>
              <span className="text-xs text-[var(--color-text-tertiary)] italic">Processing...</span>
            </motion.div>
          )}
        </div>

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
