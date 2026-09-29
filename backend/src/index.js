// Discharge Transition Exception Coordinator — backend API skeleton.
//
// Express server exposing health, case catalog, and agent invoke endpoints. Runs a
// local multi-agent orchestrator stub today; swaps to a Foundry hosted agent later
// without changing the API contract. Also serves the built React UI as static content
// when a dist build is present, mirroring the reference deployment pattern.

const path = require("path");
const fs = require("fs");
const express = require("express");
const cors = require("cors");
const morgan = require("morgan");

const { correlationId } = require("./middleware/correlationId");
const casesRoutes = require("./routes/cases");
const agentRoutes = require("./routes/agent");
const tasksRoutes = require("./routes/tasks");
const logsRoutes = require("./routes/logs");
const { logBuffer } = require("./logs/logBuffer");

const app = express();
const PORT = process.env.PORT || 8080;
const HOST = process.env.HOST || "127.0.0.1";

app.set("trust proxy", 1);
app.use(cors({ origin: process.env.FRONTEND_URL || "*" }));
app.use(morgan("dev"));
// Mirror each request line into the in-memory log buffer (clean, no ANSI) for the UI log panel.
app.use(
  morgan(":method :url :status :response-time ms", {
    stream: { write: (line) => logBuffer.push({ level: "http", message: line }) },
  }),
);
app.use(express.json({ limit: "2mb" }));
app.use(correlationId);

// Public health endpoint — no auth.
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "discharge-transition-backend", timestamp: new Date().toISOString() });
});

app.use("/api/v1/cases", casesRoutes);
app.use("/api/v1/agent", agentRoutes);
app.use("/api/v1/tasks", tasksRoutes);
app.use("/api/v1/logs", logsRoutes);

// Optionally serve the built UI (app/readmission-review-tracker/dist) at root so the
// whole demo can run from one process. Skipped gracefully if no build exists.
function resolveUiDist() {
  const candidates = [
    path.join(__dirname, "..", "..", "app", "readmission-review-tracker", "dist"),
    path.join(process.cwd(), "app", "readmission-review-tracker", "dist"),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "index.html"))) return candidate;
  }
  return null;
}

const uiDist = resolveUiDist();
if (uiDist) {
  app.use(express.static(uiDist));
}

app.listen(PORT, HOST, () => {
  // eslint-disable-next-line no-console
  console.log(`[discharge-transition-backend] listening on http://${HOST}:${PORT}`);
  // eslint-disable-next-line no-console
  console.log(uiDist ? `[ui] serving static build from ${uiDist}` : "[ui] no dist build found; API only");
});

module.exports = app;
