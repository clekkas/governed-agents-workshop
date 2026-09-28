// Correlation ID middleware. Every request gets an x-correlation-id that flows
// through the orchestrator and back out on the response, so a workflow can be
// traced end to end across specialist agents, tool calls, and telemetry.

const { randomUUID } = require("crypto");

function correlationId(req, res, next) {
  const incoming = req.header("x-correlation-id");
  const id = incoming && incoming.trim() ? incoming.trim() : `trace-${randomUUID()}`;
  req.correlationId = id;
  res.locals.correlationId = id;
  res.setHeader("x-correlation-id", id);
  next();
}

module.exports = { correlationId };
