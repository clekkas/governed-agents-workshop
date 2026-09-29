// Correlation-scoped trace store — the observability spine (WI-06).
//
// Where the activity ring buffer (logs/logBuffer.js) is a flat, capped feed of recent backend
// activity, this store keeps the COMPLETE, ORDERED event list for each run, keyed by correlation ID.
// A single invoke expands into a structured event taxonomy — run start, each tool call with its
// policy decision and latency, each agent handoff, the policy decision, the HITL task creation, and
// any subsequent human transitions — so GET /api/v1/traces/:correlationId can reconstruct exactly
// what happened, in order, for one workflow.
//
// This is the local, dependency-free teaching model of distributed tracing. The graduation target
// is Application Insights / Log Analytics with the correlation ID as the KQL join key; the event
// taxonomy below maps 1:1 to custom events/dimensions there. The store is process-local and not
// durable — see docs/observability graduation notes.

const MAX_TRACES = 200;

// Event taxonomy — stable names so they map cleanly to App Insights custom events.
const EVENT = {
  RUN_STARTED: "run.started",
  TOOL_CALLED: "tool.called",
  AGENT_HANDOFF: "agent.handoff",
  POLICY_DECISION: "policy.decision",
  REVIEW_CREATED: "review.created",
  REVIEW_TRANSITION: "review.transition",
  RUN_COMPLETED: "run.completed",
};

class TraceStore {
  constructor(max = MAX_TRACES) {
    this.max = max;
    this.traces = new Map(); // correlationId -> { correlationId, caseId, createdAt, events: [] }
    this.order = []; // insertion order of correlation IDs for capping
  }

  _ensure(correlationId, caseId) {
    let trace = this.traces.get(correlationId);
    if (!trace) {
      trace = { correlationId, caseId: caseId || null, createdAt: new Date().toISOString(), events: [] };
      this.traces.set(correlationId, trace);
      this.order.push(correlationId);
      if (this.order.length > this.max) {
        const evicted = this.order.shift();
        this.traces.delete(evicted);
      }
    }
    if (caseId && !trace.caseId) trace.caseId = caseId;
    return trace;
  }

  _add(correlationId, caseId, type, detail) {
    const trace = this._ensure(correlationId, caseId);
    trace.events.push({
      seq: trace.events.length + 1,
      timestamp: new Date().toISOString(),
      type,
      ...detail,
    });
    return trace;
  }

  // Expand an invoke result into the ordered event taxonomy for its correlation ID.
  recordInvoke(result, source) {
    const cid = result.correlationId;
    const caseId = result.caseId;
    if (!cid) return;
    this._add(cid, caseId, EVENT.RUN_STARTED, {
      name: "invoke",
      source: source || "unknown",
      riskTier: result.approvedRiskScore && result.approvedRiskScore.tier,
    });
    for (const call of result.toolCalls || []) {
      this._add(cid, caseId, EVENT.TOOL_CALLED, {
        name: call.name,
        decision: call.decision,
        latencyMs: call.latencyMs,
      });
    }
    for (const hop of result.agentHandoffs || []) {
      this._add(cid, caseId, EVENT.AGENT_HANDOFF, {
        name: hop.agentName,
        role: hop.role,
        status: hop.status,
        handoffTo: hop.handoffTo || null,
      });
    }
    this._add(cid, caseId, EVENT.POLICY_DECISION, { decision: result.policyDecision });
    this._add(cid, caseId, EVENT.RUN_COMPLETED, {
      requiresHumanReview: Boolean(result.requiresHumanReview),
    });
  }

  // Record the initial HITL task creation (PendingReview or Escalated on run).
  recordReviewCreated(task) {
    if (!task || !task.correlationId) return;
    this._add(task.correlationId, task.caseId, EVENT.REVIEW_CREATED, {
      status: task.status,
      dueAt: task.dueAt || null,
    });
  }

  // Record a human/system HITL transition.
  recordTransition(correlationId, task, action, actor) {
    if (!correlationId) return;
    this._add(correlationId, task && task.caseId, EVENT.REVIEW_TRANSITION, {
      action,
      actor: actor || "unknown",
      to: task && task.status,
    });
  }

  get(correlationId) {
    return this.traces.get(correlationId) || null;
  }

  list() {
    return this.order
      .map((cid) => this.traces.get(cid))
      .filter(Boolean)
      .map((t) => ({
        correlationId: t.correlationId,
        caseId: t.caseId,
        createdAt: t.createdAt,
        eventCount: t.events.length,
      }))
      .reverse();
  }
}

const traceStore = new TraceStore();

module.exports = { traceStore, TraceStore, EVENT };
