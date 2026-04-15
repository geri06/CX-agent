const API_BASE = '/api';

/**
 * Fetch a mock DB collection.
 * @param {'restaurants'|'invoices'|'ingredients'|'recipes'} collection
 */
export async function fetchCollection(collection) {
  const res = await fetch(`${API_BASE}/db/${collection}`);
  if (!res.ok) throw new Error(`Failed to fetch ${collection}: ${res.status}`);
  const json = await res.json();
  return json.data;
}

/**
 * Run the L2 agent and consume SSE events via a callback.
 * @param {{ user_name: string, user_email: string, user_query: string }} payload
 * @param {(event: object) => void} onEvent — called for each SSE event
 * @param {() => void} onDone — called when the stream ends
 * @param {(error: Error) => void} onError — called on error
 * @returns {AbortController} — call `.abort()` to cancel
 */
export function runAgent(payload, onEvent, onDone, onError) {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/run-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error(`Agent request failed: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.slice(6));
              onEvent(data);
            } catch (e) {
              // skip malformed events
            }
          }
        }
      }

      onDone();
    } catch (err) {
      if (err.name !== 'AbortError') {
        onError(err);
      }
    }
  })();

  return controller;
}
