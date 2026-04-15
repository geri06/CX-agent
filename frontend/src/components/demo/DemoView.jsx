import { useState, useCallback, useRef } from 'react';
import { runAgent } from '../../lib/api';
import TicketPanel from './TicketPanel';
import TracePanel from './TracePanel';
import InspectorPanel from './InspectorPanel';
import HitlControls from './HitlControls';

const DEMO_TICKET = {
  scenarioName: 'L2 — Carlos: Beer miscat + truffle oil',
  userName: 'Carlos Ruiz',
  userEmail: 'carlos@burgerhousecarlos.com',
  userQuery:
    "My food cost is at 55% which is killing my business. I use quality ingredients but it shouldn't be that high. Also my 'Smash Burger' recipe cost seems really inflated — the app says it costs €45 to make a single burger. Something is wrong.",
};

export default function DemoView() {
  const [ticket, setTicket] = useState(DEMO_TICKET);
  const [steps, setSteps] = useState([]);
  const [activeNodeId, setActiveNodeId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState(null);
  const threadIdRef = useRef(null);
  const controllerRef = useRef(null);

  const startAgent = useCallback((isResume = false, hitlResponse = null) => {
    if (!isResume) {
      setSteps([]);
      setActiveNodeId(null);
      threadIdRef.current = null;
    }
    
    setIsRunning(true);
    setIsPaused(false);
    setIsDone(false);
    setError(null);

    const payload = {
      user_name: ticket.userName,
      user_email: ticket.userEmail,
      user_query: ticket.userQuery,
    };

    if (isResume) {
      payload.thread_id = threadIdRef.current;
      payload.hitl_response = hitlResponse;
    }

    const controller = runAgent(
      payload,
      // onEvent
      (event) => {
        if (event.output?.thread_id) {
          threadIdRef.current = event.output.thread_id;
        }

        if (event.status === 'paused') {
          setIsPaused(true);
        }

        const step = {
          id: `${event.node_id}_${event.step || Date.now()}`,
          nodeId: event.node_id,
          label: event.label,
          type: event.type,
          status: event.status,
          description: event.description,
          output: event.output || {},
          timestamp: new Date().toISOString(),
        };

        setSteps((prev) => [...prev, step]);
        setActiveNodeId(step.id);
      },
      // onDone
      () => {
        setIsRunning(false);
        // If it was just paused, we don't mark as done
        setIsDone((prevIsDone) => {
           // Hack to access current state: if not paused, we must be fully done
           return true; 
        });
      },
      // onError
      (err) => {
        setIsRunning(false);
        setError(err.message);
      }
    );

    controllerRef.current = controller;
  }, [ticket]);

  // Find the active step's data for the inspector
  const activeStep = steps.find((s) => s.id === activeNodeId) || null;

  return (
    <div className="flex flex-col h-full p-10 gap-8 bg-[var(--color-bg-primary)] shrink">
      <div className="flex h-full gap-8 shrink min-h-0">
        {/* Panel 1: Input & Context (25%) */}
        <div className="w-[25%] h-full shrink-0 flex flex-col border border-[var(--color-border)] rounded-xl overflow-y-auto bg-[var(--color-bg-surface)] shadow-sm">
          <TicketPanel
            ticket={ticket}
            setTicket={setTicket}
            isRunning={isRunning && !isPaused}
            isDone={isDone && !isPaused}
            error={error}
            onRun={() => startAgent(false)}
          />
        </div>

        {/* Panel 2: Thinking Trace (35%) */}
        <div className="w-[35%] h-full shrink-0 border border-[var(--color-border)] rounded-xl overflow-y-auto bg-[var(--color-bg-surface)] shadow-sm">
          <TracePanel
            steps={steps}
            activeNodeId={activeNodeId}
            isRunning={isRunning && !isPaused}
            onStepClick={setActiveNodeId}
          />
        </div>

        {/* Panel 3: Node Output Inspector (40%) */}
        <div className="flex-1 h-full min-w-0 border border-[var(--color-border)] rounded-xl overflow-hidden shadow-sm flex flex-col relative">
          <InspectorPanel
            activeStep={activeStep}
            isRunning={isRunning && !isPaused}
          />
          {isPaused && (
            <div className="absolute bottom-4 left-4 right-4 z-10">
              <HitlControls 
                draftEmail={activeStep?.output?.draft_email}
                threadId={threadIdRef.current}
                onResume={(hitlResponse) => startAgent(true, hitlResponse)} 
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
