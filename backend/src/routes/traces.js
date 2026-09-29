// GET /api/v1/traces           — list recent traces (correlationId, caseId, eventCount).
// GET /api/v1/traces/:id        — the complete, ordered event list for one correlation ID.
//
// This is the WI-06 acceptance surface: a single invoke produces a complete, ordered, correlated
// event list. Dev/demo only — the durable equivalent is App Insights queried by correlation ID.

const express = require("express");
const { traceStore } = require("../observability/traceStore");

const router = express.Router();

router.get("/", (_req, res) => {
  res.json({ traces: traceStore.list() });
});

router.get("/:id", (req, res) => {
  const trace = traceStore.get(req.params.id);
  if (!trace) {
    return res.status(404).json({
      type: "about:blank",
      title: "Trace not found",
      status: 404,
      detail: `No trace for correlation id '${req.params.id}'.`,
      correlationId: res.locals.correlationId,
    });
  }
  res.json(trace);
});

module.exports = router;
