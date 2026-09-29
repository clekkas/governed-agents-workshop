// HITL review-task routes — the Data Task Scheduler approval gate on the app path.
//
// Operates on the shared in-memory task store (backend/src/hitl/taskStore.js), which every
// successful invoke registers into. Mirrors the agent-service FastAPI task endpoints so the UI
// contract is identical whether the backend runs standalone or delegates to the Python service.

const express = require("express");
const { store, HitlError } = require("../hitl/taskStore");
const { logBuffer } = require("../logs/logBuffer");
const { traceStore } = require("../observability/traceStore");

const router = express.Router();

function sendError(res, err) {
  const status = err instanceof HitlError ? err.status : 500;
  return res.status(status).json({
    type: "about:blank",
    title: "HITL transition error",
    status,
    detail: err.message,
    correlationId: res.locals.correlationId,
  });
}

// GET /api/v1/tasks
router.get("/", (_req, res) => {
  res.json({ tasks: store.list() });
});

// GET /api/v1/tasks/:id
router.get("/:id", (req, res) => {
  try {
    res.json(store.get(req.params.id));
  } catch (err) {
    sendError(res, err);
  }
});

// GET /api/v1/tasks/:id/audit
router.get("/:id/audit", (req, res) => {
  try {
    res.json({ taskId: req.params.id, audit: store.audit(req.params.id) });
  } catch (err) {
    sendError(res, err);
  }
});

// POST /api/v1/tasks/:id/action  Body: { action, actor, note }
router.post("/:id/action", (req, res) => {
  const { action, actor, note } = req.body || {};
  try {
    const task = store.applyAction(req.params.id, action, actor, note);
    traceStore.recordTransition(req.params.id, task, action, actor);
    logBuffer.event(
      `HITL ${action} by ${actor || "unknown"} → ${task.status} · ${task.caseId}`,
      req.params.id,
    );
    res.json(task);
  } catch (err) {
    logBuffer.push({
      level: "warn",
      message: `HITL ${action} rejected (${err.status}): ${err.message}`,
      correlationId: req.params.id,
    });
    sendError(res, err);
  }
});

// POST /api/v1/tasks/sweep — force the timer->escalate sweep (demo fast-forward).
router.post("/sweep", (_req, res) => {
  const escalated = store.sweep();
  if (escalated.length) {
    logBuffer.event(`HITL sweep auto-escalated ${escalated.length} overdue task(s)`);
  }
  res.json({ escalated: escalated.map((t) => t.taskId), count: escalated.length });
});

module.exports = router;
