import { useState } from 'react';
import { Check, Edit3, Send } from 'lucide-react';

export default function HitlControls({ draftEmail, threadId, onResume }) {
  const [feedback, setFeedback] = useState('');
  const [mode, setMode] = useState('decision'); // 'decision' | 'revision'

  const handleApprove = () => {
    onResume({ decision: 'approve', feedback: '' });
  };

  const handleRequestRevision = () => {
    onResume({ decision: 'request_revision', feedback });
  };

  return (
    <div className="border border-[var(--color-border)] rounded-xl bg-white p-5 shadow-lg mt-4 animate-in fade-in slide-in-from-bottom-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-[var(--color-accent)] flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-accent)] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[var(--color-accent)]"></span>
          </span>
          Awaiting Human Approval
        </h3>
        <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
          The agent has drafted an email. Please review it in the Inspector panel.
        </p>
      </div>

      {mode === 'decision' ? (
        <div className="flex items-center gap-3">
          <button
            onClick={handleApprove}
            className="flex-1 bg-[var(--color-success)] text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-[var(--color-success-muted)] transition-colors"
          >
            <Check size={16} />
            Approve & Send
          </button>
          <button
            onClick={() => setMode('revision')}
            className="flex-1 bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)] font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-[var(--color-border)] transition-colors"
          >
            <Edit3 size={16} />
            Request Revision
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Type your feedback to improve the draft..."
            className="w-full text-[13px] p-3 border border-[var(--color-border)] rounded-lg focus:outline-none focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent-glow)] min-h-[80px] resize-none"
            autoFocus
          />
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMode('decision')}
              className="px-4 py-2 text-xs font-medium text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)]"
            >
              Cancel
            </button>
            <button
              onClick={handleRequestRevision}
              disabled={!feedback.trim()}
              className="flex-1 bg-[var(--color-accent)] text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-[var(--color-accent-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={16} />
              Submit Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
