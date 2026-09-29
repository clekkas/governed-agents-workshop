// Backend endpoint tests (Node built-in test runner + http + fetch; no external deps).
// Mounts the exported Express app on an ephemeral port so nothing binds 8080 during tests.
// Run: node --test  (from the backend/ folder)

const { test, before, after } = require("node:test");
const assert = require("node:assert");
const http = require("node:http");
const app = require("../src/index");

let server;
let base;

before(async () => {
  server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  base = `http://127.0.0.1:${port}`;
});

after(async () => {
  await new Promise((resolve) => server.close(resolve));
});

test("GET /api/health returns ok", async () => {
  const res = await fetch(`${base}/api/health`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.status, "ok");
});

test("GET /api/v1/cases returns the worklist", async () => {
  const res = await fetch(`${base}/api/v1/cases`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.ok(Array.isArray(body.cases) && body.cases.length >= 1, "expected at least one case");
  assert.ok(body.cases.some((c) => c.id === "P0147"), "expected P0147 in the worklist");
});

test("GET /api/v1/cases/:id returns 200 for a known case", async () => {
  const res = await fetch(`${base}/api/v1/cases/P0147`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.id, "P0147");
});

test("GET /api/v1/cases/:id returns 404 for an unknown case", async () => {
  const res = await fetch(`${base}/api/v1/cases/NOPE`);
  assert.equal(res.status, 404);
  const body = await res.json();
  assert.equal(body.status, 404);
  assert.ok(body.correlationId, "problem response should carry a correlationId");
});

test("POST /api/v1/agent/invoke returns 200 and requires human review", async () => {
  const res = await fetch(`${base}/api/v1/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caseId: "P0147" }),
  });
  assert.equal(res.status, 200);
  assert.ok(res.headers.get("x-correlation-id"), "response should carry x-correlation-id");
  const body = await res.json();
  assert.equal(body.requiresHumanReview, true);
  assert.equal(body.caseId, "P0147");
  assert.ok(Array.isArray(body.evidence) && body.evidence.length >= 1, "expected cited evidence");
});

test("POST /api/v1/agent/invoke returns 400 when caseId is missing", async () => {
  const res = await fetch(`${base}/api/v1/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  assert.equal(res.status, 400);
  const body = await res.json();
  assert.equal(body.status, 400);
});

test("POST /api/v1/agent/invoke returns 404 for an unknown case", async () => {
  const res = await fetch(`${base}/api/v1/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caseId: "NOPE" }),
  });
  assert.equal(res.status, 404);
});

test("P0310 escalates (missing specialty protocol)", async () => {
  const res = await fetch(`${base}/api/v1/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caseId: "P0310" }),
  });
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.policyDecision, "escalate");
  assert.equal(body.requiresHumanReview, true);
});
