// Durable HITL task store — Node mirror of agent-service/.../hitl.py.
//
// This is the source of truth for the review-task lifecycle on the app path (UI -> backend).
// Every successful invoke registers a task here; the UI reads and acts on it. The state machine,
// audit contract, and timeout->escalate branch match the Python store and the Durable Task
// Scheduler reference in agent-service/orchestrations/. In-memory is sufficient for the
// single-process workshop backend; the Python store adds file persistence, the DTS backend adds
// distributed durability.

const PENDING = "PendingReview";
const IN_REVIEW = "InReview";
const APPROVED = "Approved";
const NEEDS_REWORK = "NeedsRework";
const REJECTED = "Rejected";
const ESCALATED = "Escalated";

const TERMINAL = new Set([APPROVED, REJECTED, ESCALATED]);

const TRANSITIONS = {
  claim: { [PENDING]: IN_REVIEW },
  approve: { [PENDING]: APPROVED, [IN_REVIEW]: APPROVED },
  request_changes: { [PENDING]: NEEDS_REWORK, [IN_REVIEW]: NEEDS_REWORK },
  reject: { [PENDING]: REJECTED, [IN_REVIEW]: REJECTED },
  escalate: { [PENDING]: ESCALATED, [IN_REVIEW]: ESCALATED, [NEEDS_REWORK]: ESCALATED },
  rework: { [NEEDS_REWORK]: PENDING },
};

const HUMAN_ONLY = new Set(["approve", "reject"]);
const AGENT_ACTORS = new Set(["agent", "orchestrator", "system", ""]);

const SLA_SECONDS = parseInt(process.env.HITL_SLA_SECONDS || "86400", 10);

class HitlError extends Error {
  constructor(message, status = 409) {
    super(message);
    this.status = status;
  }
}

function nowIso() {
  return new Date().toISOString();
}

class TaskStore {
  constructor(slaSeconds = SLA_SECONDS) {
    this.slaSeconds = slaSeconds;
    this.tasks = new Map();
  }

  registerFromResult(result, reviewCase = {}) {
    const taskId = result.correlationId;
    const escalate = result.policyDecision === "escalate";
    const status = escalate ? ESCALATED : PENDING;
    const created = new Date();
    const due = new Date(created.getTime() + this.slaSeconds * 1000);
    const task = {
      taskId,
      correlationId: taskId,
      caseId: result.caseId,
      patientLabel: reviewCase.patientLabel,
      facility: reviewCase.facility,
      diagnosis: reviewCase.diagnosis,
      riskTier: result.approvedRiskScore && result.approvedRiskScore.tier,
      status,
      assignedRole: null,
      policyDecision: result.policyDecision,
      transitionGaps: result.transitionGaps || [],
      missingInformation: result.missingInformation || [],
      draftPlan: result.draftExceptionPacket || [],
      evidence: result.evidence || [],
      createdAt: created.toISOString(),
      updatedAt: created.toISOString(),
      dueAt: due.toISOString(),
      history: [
        {
          timestamp: created.toISOString(),
          from: null,
          to: status,
          action: escalate ? "escalate" : "create",
          actor: "orchestrator",
          note: escalate
            ? "Policy escalation on run — routed to specialist reviewer."
            : "Draft exception packet created; awaiting care-manager review.",
        },
      ],
    };
    this.tasks.set(taskId, task);
    return task;
  }

  list() {
    this.sweep();
    return [...this.tasks.values()].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
  }

  get(taskId) {
    this.sweep();
    const task = this.tasks.get(taskId);
    if (!task) throw new HitlError(`No review task for correlation id '${taskId}'.`, 404);
    return task;
  }

  audit(taskId) {
    return this.get(taskId).history;
  }

  applyAction(taskId, action, actor = "", note = "") {
    action = (action || "").trim().toLowerCase();
    if (!TRANSITIONS[action]) {
      throw new HitlError(`Unknown action '${action}'. Valid: ${Object.keys(TRANSITIONS).join(", ")}.`, 400);
    }
    const task = this.tasks.get(taskId);
    if (!task) throw new HitlError(`No review task for correlation id '${taskId}'.`, 404);

    const current = task.status;
    if (TERMINAL.has(current)) {
      throw new HitlError(`Task is already ${current}; no further transitions are allowed.`, 409);
    }
    const dest = TRANSITIONS[action][current];
    if (!dest) throw new HitlError(`Action '${action}' is not valid from state '${current}'.`, 409);
    if (HUMAN_ONLY.has(action) && AGENT_ACTORS.has((actor || "").trim().toLowerCase())) {
      throw new HitlError(`Action '${action}' requires a human reviewer; supply an 'actor'.`, 403);
    }
    this.transition(task, action, current, dest, actor, note);
    return task;
  }

  sweep() {
    const now = Date.now();
    const escalated = [];
    for (const task of this.tasks.values()) {
      if (TERMINAL.has(task.status)) continue;
      if (task.dueAt && new Date(task.dueAt).getTime() <= now) {
        this.transition(
          task,
          "escalate",
          task.status,
          ESCALATED,
          "system",
          "Review SLA elapsed with no decision; auto-escalated to a human reviewer."
        );
        escalated.push(task);
      }
    }
    return escalated;
  }

  transition(task, action, src, dst, actor, note) {
    task.status = dst;
    task.updatedAt = nowIso();
    if (action === "claim") task.assignedRole = actor || task.assignedRole;
    task.history.push({
      timestamp: nowIso(),
      from: src,
      to: dst,
      action,
      actor: actor || "orchestrator",
      note: note || "",
    });
  }
}

// Shared singleton — both the agent invoke route and the tasks route use this instance.
const store = new TaskStore();

module.exports = { store, TaskStore, HitlError };
