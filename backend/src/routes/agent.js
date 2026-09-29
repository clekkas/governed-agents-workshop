// Agent invoke route.
//
// By default this runs the in-process local orchestrator stub. If AGENT_SERVICE_URL is
// set (the Python code-first agent service, or later a Foundry hosted agent endpoint that
// speaks the same contract), the request is delegated there instead. On delegation failure
// it falls back to the local orchestrator so the demo stays resilient. Either way the
// response contract and x-correlation-id are identical.

const express = require("express");
const { getCase } = require("../data/cases");
const { runOrchestrator } = require("../orchestrator/localOrchestrator");
const { store } = require("../hitl/taskStore");
const { logBuffer } = require("../logs/logBuffer");

const router = express.Router();

const AGENT_SERVICE_URL = (process.env.AGENT_SERVICE_URL || "").trim();

async function delegate(caseId, actorRole, correlationId) {
  const base = AGENT_SERVICE_URL.replace(/\/+$/, "");
  const res = await fetch(`${base}/api/v1/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-correlation-id": correlationId },
    body: JSON.stringify({ caseId, actorRole }),
  });
  if (!res.ok) {
    throw new Error(`agent service responded ${res.status}`);
  }
  return res.json();
}

// POST /api/v1/agent/invoke
// Body: { caseId: string, actorRole?: string }
router.post("/invoke", async (req, res) => {
  const { caseId, actorRole } = req.body || {};
  if (!caseId || typeof caseId !== "string") {
    return res.status(400).json({
      type: "about:blank",
      title: "Invalid request",
      status: 400,
      detail: "Body must include a string 'caseId'.",
      correlationId: res.locals.correlationId,
    });
  }

  const reviewCase = getCase(caseId);
  if (!reviewCase) {
    return res.status(404).json({
      type: "about:blank",
      title: "Case not found",
      status: 404,
      detail: `No synthetic case with id '${caseId}'.`,
      correlationId: res.locals.correlationId,
    });
  }

  if (AGENT_SERVICE_URL) {
    try {
      const result = await delegate(caseId, actorRole, res.locals.correlationId);
      res.setHeader("x-agent-source", "agent-service");
      // Register the durable review task so the UI's approval gate has state to act on.
      const task = store.registerFromResult(result, reviewCase);
      logBuffer.event(
        `invoke ${caseId} → agent-service · policy=${result.policyDecision} · task=${task.status}`,
        res.locals.correlationId,
      );
      return res.json(result);
    } catch (err) {
      // Resilient fallback: log and use the local orchestrator.
      // eslint-disable-next-line no-console
      console.warn(`[agent] delegation to ${AGENT_SERVICE_URL} failed: ${err.message}; using local orchestrator`);
      res.setHeader("x-agent-source", "local-fallback");
      const local = runOrchestrator(reviewCase, res.locals.correlationId);
      const task = store.registerFromResult(local, reviewCase);
      logBuffer.event(
        `invoke ${caseId} → local-fallback (agent-service unreachable) · task=${task.status}`,
        res.locals.correlationId,
      );
      return res.json(local);
    }
  }

  res.setHeader("x-agent-source", "local");
  const local = runOrchestrator(reviewCase, res.locals.correlationId);
  const task = store.registerFromResult(local, reviewCase);
  logBuffer.event(
    `invoke ${caseId} → local · policy=${local.policyDecision} · task=${task.status}`,
    res.locals.correlationId,
  );
  res.json(local);
});

module.exports = router;
