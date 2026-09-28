// Case catalog routes. Serves the synthetic discharge-transition cases that the
// UI worklist and batch queue render.

const express = require("express");
const { listCases, getCase } = require("../data/cases");

const router = express.Router();

// GET /api/v1/cases — worklist summary.
router.get("/", (_req, res) => {
  res.json({ cases: listCases() });
});

// GET /api/v1/cases/:id — full case payload envelope.
router.get("/:id", (req, res) => {
  const reviewCase = getCase(req.params.id);
  if (!reviewCase) {
    return res.status(404).json({
      type: "about:blank",
      title: "Case not found",
      status: 404,
      detail: `No synthetic case with id '${req.params.id}'.`,
      correlationId: res.locals.correlationId,
    });
  }
  res.json(reviewCase);
});

module.exports = router;
