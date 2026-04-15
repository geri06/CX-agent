import { useEffect, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Brain, Wrench, Eye, ChevronDown } from 'lucide-react';
import TypewriterText from './TypewriterText';

/**
 * Syntax-highlighted JSON renderer
 */
function SyntaxJSON({ data, indent = 0 }) {
  const json = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  if (!json) return null;

  const lines = json.split('\n');
  return (
    <div className="text-[13px] leading-[1.7]">
      {lines.map((line, i) => (
        <div key={i}>{colorize(line)}</div>
      ))}
    </div>
  );
}

function colorize(line) {
  // Colorize JSON syntax
  const parts = [];
  let remaining = line;
  let key = 0;

  // Match key: value patterns
  const keyMatch = remaining.match(/^(\s*)"([^"]+)"(\s*:\s*)/);
  if (keyMatch) {
    parts.push(<span key={key++}>{keyMatch[1]}</span>);
    parts.push(<span key={key++} className="syntax-key">"{keyMatch[2]}"</span>);
    parts.push(<span key={key++} className="syntax-colon">{keyMatch[3]}</span>);
    remaining = remaining.slice(keyMatch[0].length);
  }

  // Match values
  if (remaining.match(/^\s*"[^"]*"[,]?\s*$/)) {
    const m = remaining.match(/^(\s*"[^"]*")([,]?\s*)$/);
    if (m) {
      parts.push(<span key={key++} className="syntax-string">{m[1]}</span>);
      parts.push(<span key={key++} className="syntax-bracket">{m[2]}</span>);
      return parts.length > 0 ? parts : line;
    }
  }

  if (remaining.match(/^\s*-?\d+\.?\d*[,]?\s*$/)) {
    const m = remaining.match(/^(\s*-?\d+\.?\d*)([,]?\s*)$/);
    if (m) {
      parts.push(<span key={key++} className="syntax-number">{m[1]}</span>);
      parts.push(<span key={key++} className="syntax-bracket">{m[2]}</span>);
      return parts.length > 0 ? parts : line;
    }
  }

  if (remaining.match(/^\s*(true|false)[,]?\s*$/)) {
    const m = remaining.match(/^(\s*(?:true|false))([,]?\s*)$/);
    if (m) {
      parts.push(<span key={key++} className="syntax-boolean">{m[1]}</span>);
      parts.push(<span key={key++} className="syntax-bracket">{m[2]}</span>);
      return parts.length > 0 ? parts : line;
    }
  }

  if (remaining.match(/^\s*null[,]?\s*$/)) {
    const m = remaining.match(/^(\s*null)([,]?\s*)$/);
    if (m) {
      parts.push(<span key={key++} className="syntax-null">{m[1]}</span>);
      parts.push(<span key={key++} className="syntax-bracket">{m[2]}</span>);
      return parts.length > 0 ? parts : line;
    }
  }

  // Brackets
  if (remaining.match(/^[\s{}[\],]*$/)) {
    parts.push(<span key={key++} className="syntax-bracket">{remaining}</span>);
    return parts.length > 0 ? parts : line;
  }

  parts.push(<span key={key++}>{remaining}</span>);
  return parts.length > 0 ? parts : line;
}

/**
 * Extract the reasoning / thought content from a step's output
 */
function extractReasoningContent(step) {
  if (!step?.output) return null;
  const { output } = step;

  // Show draft email on Agent Complete or Awaiting Human Review
  if ((step.nodeId === '__end__' || step.nodeId === '__interrupt__') && output.draft_email) {
    return output.draft_email;
  }

  // Check for messages with content or reasoning_content (reasoner nodes)
  if (output.messages && Array.isArray(output.messages)) {
    for (const msg of output.messages) {
      // 1. Direct content field (non-empty)
      if (msg.content && typeof msg.content === 'string' && msg.content.trim().length > 0) {
        return msg.content;
      }
      // 2. kwargs.content (non-empty)
      if (msg.kwargs?.content && typeof msg.kwargs.content === 'string' && msg.kwargs.content.trim().length > 0) {
        return msg.kwargs.content;
      }
      // 3. Fallback: additional_kwargs.reasoning_content (when content is empty)
      if (msg.additional_kwargs?.reasoning_content && typeof msg.additional_kwargs.reasoning_content === 'string') {
        return msg.additional_kwargs.reasoning_content;
      }
      // 4. Fallback: kwargs.additional_kwargs.reasoning_content
      if (msg.kwargs?.additional_kwargs?.reasoning_content && typeof msg.kwargs.additional_kwargs.reasoning_content === 'string') {
        return msg.kwargs.additional_kwargs.reasoning_content;
      }
    }
  }

  // Check for direct content fields
  if (output.reasoning_content) return output.reasoning_content;
  if (output.investigation_context) return output.investigation_context;
  if (output.draft_email) return output.draft_email;
  if (output.feedback) return output.feedback;

  return null;
}

/**
 * Extract tool call information
 */
function extractToolCalls(step) {
  if (!step?.output?.messages) return null;
  const toolCalls = [];
  for (const msg of step.output.messages) {
    if (msg.tool_calls && msg.tool_calls.length > 0) {
      toolCalls.push(...msg.tool_calls);
    }
  }
  return toolCalls.length > 0 ? toolCalls : null;
}

export default function InspectorPanel({ activeStep, isRunning }) {
  const scrollRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const contentRef = useRef(null);

  // Auto-scroll when content changes
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeStep, autoScroll]);

  // Detect manual scroll
  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 30;
    setAutoScroll(atBottom);
  };

  const reasoningContent = useMemo(() => extractReasoningContent(activeStep), [activeStep]);
  const toolCalls = useMemo(() => extractToolCalls(activeStep), [activeStep]);
  const isReasonerType = activeStep?.type === 'reasoner';
  const isToolType = activeStep?.type === 'tool';

  return (
    <div className="h-full flex flex-col bg-[var(--color-bg-surface)]">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <Terminal size={14} className="text-[var(--color-accent-hover)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-primary)] tracking-tight font-mono">
            Inspector
          </h2>
          {activeStep && (
            <span className={`badge text-[9px] ${
              isReasonerType ? 'badge-accent' : isToolType ? 'badge-blue' : 'badge-neutral'
            }`}>
              {activeStep.type}
            </span>
          )}
        </div>
        {activeStep && (
          <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-tertiary)] font-mono">
            <span>{activeStep.label}</span>
            {!autoScroll && (
              <button
                onClick={() => {
                  setAutoScroll(true);
                  scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
                }}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[var(--color-bg-elevated)] hover:bg-[var(--color-accent)]/20 transition-colors cursor-pointer"
              >
                <ChevronDown size={10} />
                Auto-scroll
              </button>
            )}
          </div>
        )}
      </div>

      {/* Content */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6"
      >
        <AnimatePresence mode="wait">
          {!activeStep ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center h-48"
            >
              <div className="text-center">
                <Eye size={28} className="mx-auto mb-2 text-[var(--color-text-tertiary)]/30" />
                <p className="text-sm text-[var(--color-text-tertiary)]/60">Select a node to inspect</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key={activeStep.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              ref={contentRef}
            >
              {/* Formatted content: reasoning, draft email, or human review */}
              {(isReasonerType || activeStep.nodeId === '__end__' || activeStep.nodeId === '__interrupt__' || activeStep.nodeId === '__resume__') && reasoningContent && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Brain size={14} className="text-[var(--color-accent-hover)]" />
                    <span className="text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">
                      {activeStep.nodeId === 'extract_findings_node' ? 'Investigation Findings' :
                       activeStep.nodeId === 'l2_draft_node' ? 'Draft Email' :
                       activeStep.nodeId === '__end__' ? 'Final Draft Email' :
                       activeStep.nodeId === '__interrupt__' ? 'Drafted Email — Awaiting Review' :
                       activeStep.nodeId === '__resume__' ? 'Human Feedback' :
                       'Reasoning'}
                    </span>
                  </div>
                  <div className="code-block text-[var(--color-text-primary)] whitespace-pre-wrap">
                    <TypewriterText text={reasoningContent} speed={2} />
                  </div>
                </div>
              )}

              {/* Tool calls display */}
              {toolCalls && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Wrench size={14} className="text-[var(--color-blue)]" />
                    <span className="text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">
                      Tool Calls
                    </span>
                  </div>
                  {toolCalls.map((tc, i) => (
                    <div key={i} className="mb-3">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="badge badge-blue font-mono text-[10px]">{tc.name}</span>
                      </div>
                      <div className="code-block">
                        <SyntaxJSON data={tc.args} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Raw output (always shown as fallback or for tool executor with tool results) */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Terminal size={14} className="text-[var(--color-text-tertiary)]" />
                  <span className="text-[11px] font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider">
                    Node Output
                  </span>
                </div>
                <div className="code-block">
                  <SyntaxJSON data={activeStep.output} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
