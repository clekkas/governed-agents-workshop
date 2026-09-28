// Agent invoke route. Runs the local multi-agent orchestrator stub for a case and
// returns the discharge-transition exception packet. The response contract is the
// one a Microsoft Foundry hosted agent will fulfill later without changing callers.

const express = require("express");
const { getCase } = require("../data/cases");
const { runOrchestrator } = require("../orchestrator/localOrchestrator");

const router = express.Router();

// POST /api/v1/agent/invoke
// Body: { caseId: string, actorRole?: string }
router.post("/invoke", (req, res) => {
  const { caseId } = req.body || {};
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

  const result = runOrchestrator(reviewCase, res.locals.correlationId);
  res.json(result);
});

module.exports = router;
