// In-memory ring buffer of recent backend activity — a lightweight, dependency-free preview of the
// observability story (WI-06). Captures HTTP request lines (via morgan) and structured domain
// events (invoke, HITL transitions), and exposes them through GET /api/v1/logs so the UI can show a
// live backend activity feed. This is NOT durable telemetry — App Insights / Log Analytics is the
// real sink; this buffer just makes the flow visible in the workshop demo.

const MAX_ENTRIES = 200;

class LogBuffer {
  constructor(max = MAX_ENTRIES) {
    this.max = max;
    this.entries = [];
    this.seq = 0;
  }

  push({ level = "info", message, correlationId = null }) {
    const entry = {
      seq: ++this.seq,
      timestamp: new Date().toISOString(),
      level,
      message: String(message || "").trim(),
      correlationId,
    };
    this.entries.push(entry);
    if (this.entries.length > this.max) {
      this.entries.splice(0, this.entries.length - this.max);
    }
    return entry;
  }

  // Structured domain event (invoke, task transition, policy escalation, etc.).
  event(message, correlationId = null) {
    return this.push({ level: "event", message, correlationId });
  }

  // Return entries with seq greater than `sinceSeq` (0 = all), newest last, capped at `limit`.
  list(sinceSeq = 0, limit = 100) {
    const filtered = this.entries.filter((e) => e.seq > sinceSeq);
    return filtered.slice(-limit);
  }
}

const logBuffer = new LogBuffer();

module.exports = { logBuffer, LogBuffer };
