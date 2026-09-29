// GET /api/v1/logs — recent backend activity for the UI's live log panel.
// Query: ?since=<seq> to fetch only newer entries; ?limit=<n> (default 100).

const express = require("express");
const { logBuffer } = require("../logs/logBuffer");

const router = express.Router();

router.get("/", (req, res) => {
  const since = parseInt(req.query.since, 10) || 0;
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 200);
  const logs = logBuffer.list(since, limit);
  const lastSeq = logs.length ? logs[logs.length - 1].seq : since;
  res.json({ logs, lastSeq });
});

module.exports = router;
