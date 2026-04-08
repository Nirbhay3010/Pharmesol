const API_BASE = "http://localhost:8000";

export async function startSession(phone) {
  const res = await fetch(`${API_BASE}/api/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function streamMessage(sessionId, message, onToken, onDone, onRetract) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok) throw new Error("Failed to send message");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.retract && onRetract) {
            onRetract(data.replacement);
          } else if (data.token) {
            onToken(data.token);
          } else if (data.done) {
            onDone(data.actions || []);
          } else if (data.error) {
            onDone([], data.error);
          }
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}
