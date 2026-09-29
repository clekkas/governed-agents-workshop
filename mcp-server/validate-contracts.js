// MCP tool contract validation (WI-02).
//
// Validates that the arguments the agent sends to each governed MCP tool conform to the published
// JSON Schema in mcp-server/tool-contracts/. Dependency-free: includes a small JSON Schema validator
// covering the subset those contracts use (type, required, properties, additionalProperties, enum,
// items, minimum/maximum). Exits non-zero and prints the offending path if anything drifts.
//
// It also runs a self-test: a deliberately-broken invocation for every tool MUST be rejected, so the
// gate proves it fails loudly rather than passing silently.
//
// Run:  node mcp-server/validate-contracts.js

const fs = require("fs");
const path = require("path");

const CONTRACTS_DIR = path.resolve(__dirname, "tool-contracts");

// ---- minimal JSON Schema validator (subset used by the tool contracts) ------------------------
function validate(schema, value, pathStr, errors) {
  const t = schema.type;
  if (t === "object") {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      errors.push(`${pathStr}: expected object`);
      return;
    }
    for (const req of schema.required || []) {
      if (!(req in value)) errors.push(`${pathStr}: missing required property '${req}'`);
    }
    const props = schema.properties || {};
    if (schema.additionalProperties === false) {
      for (const key of Object.keys(value)) {
        if (!(key in props)) errors.push(`${pathStr}: additional property '${key}' not allowed`);
      }
    }
    for (const [key, sub] of Object.entries(props)) {
      if (key in value) validate(sub, value[key], `${pathStr}.${key}`, errors);
    }
    return;
  }
  if (t === "array") {
    if (!Array.isArray(value)) {
      errors.push(`${pathStr}: expected array`);
      return;
    }
    if (schema.items) value.forEach((item, i) => validate(schema.items, item, `${pathStr}[${i}]`, errors));
    return;
  }
  if (t === "string") {
    if (typeof value !== "string") errors.push(`${pathStr}: expected string`);
    else if (schema.enum && !schema.enum.includes(value)) errors.push(`${pathStr}: '${value}' not in enum [${schema.enum.join(", ")}]`);
    return;
  }
  if (t === "boolean") {
    if (typeof value !== "boolean") errors.push(`${pathStr}: expected boolean`);
    return;
  }
  if (t === "integer" || t === "number") {
    if (typeof value !== "number" || (t === "integer" && !Number.isInteger(value))) {
      errors.push(`${pathStr}: expected ${t}`);
      return;
    }
    if (schema.minimum != null && value < schema.minimum) errors.push(`${pathStr}: ${value} < minimum ${schema.minimum}`);
    if (schema.maximum != null && value > schema.maximum) errors.push(`${pathStr}: ${value} > maximum ${schema.maximum}`);
    return;
  }
}

function validateOrThrow(schema, value) {
  const errors = [];
  validate(schema, value, "$", errors);
  return errors;
}

// ---- canonical invocations the agent sends to each tool ---------------------------------------
// This is the documented MCP invocation contract: given a case + correlation ID, these are the
// arguments the orchestrator passes to each governed tool. Validated against the published schema.
function invocations(cid) {
  return {
    "patient.get": { patientId: "P0147", correlationId: cid, purpose: "care-review" },
    "utilization.history": { patientId: "P0147", correlationId: cid, lookbackDays: 365, aggregateOnly: true },
    "risk_score.get": { patientId: "P0147", encounterId: "E1", correlationId: cid, includeDriverCodes: true },
    "protocol.search": { query: "CHF discharge follow-up", correlationId: cid, facility: "Metro General", topK: 5 },
    "task.create": {
      patientId: "P0147",
      correlationId: cid,
      draftPlan: "Confirm follow-up appointment within 48h.",
      evidence: [{ source: "CHF Follow-Up Protocol", claim: "Follow-up within 48-72h." }],
      assignedRole: "Care Manager",
    },
    "audit.write": { correlationId: cid, eventType: "task.created", actor: "orchestrator", timestamp: "2026-09-28T22:00:00Z" },
    "notes.get": { patientId: "P0147", encounterId: "E1", correlationId: cid, redactedOnly: true },
  };
}

// A deliberately-broken invocation per tool, to prove the validator rejects drift.
function drifted(cid) {
  return {
    "patient.get": { patientId: "P0147", correlationId: cid, purpose: "unauthorized-bulk-export" }, // enum violation
    "utilization.history": { correlationId: cid }, // missing required patientId
    "risk_score.get": { patientId: "P0147", encounterId: "E1", correlationId: cid, surpriseField: true }, // extra prop
    "protocol.search": { query: "x", correlationId: cid, topK: 99 }, // maximum violation
    "task.create": { patientId: "P0147", correlationId: cid, draftPlan: "x", evidence: [{ source: "s" }] }, // item missing 'claim'
    "audit.write": { correlationId: cid, eventType: "x", actor: "a" }, // missing timestamp
    "notes.get": { patientId: "P0147", correlationId: cid }, // missing encounterId
  };
}

function loadSchemas() {
  const map = {};
  for (const file of fs.readdirSync(CONTRACTS_DIR)) {
    if (!file.endsWith(".schema.json")) continue;
    const schema = JSON.parse(fs.readFileSync(path.join(CONTRACTS_DIR, file), "utf8"));
    map[schema.title] = schema;
  }
  return map;
}

function main() {
  const schemas = loadSchemas();
  const cid = "trace-contract-check";
  const valid = invocations(cid);
  const bad = drifted(cid);
  const failures = [];

  const toolNames = Object.keys(schemas).sort();
  console.log(`Validating ${toolNames.length} MCP tool contract(s) in mcp-server/tool-contracts/\n`);

  for (const name of toolNames) {
    const schema = schemas[name];

    // 1. A canonical invocation must satisfy the schema.
    if (!(name in valid)) {
      failures.push(`${name}: no canonical invocation defined in validator`);
      console.log(`  FAIL  ${name}  (no canonical invocation)`);
      continue;
    }
    const errs = validateOrThrow(schema, valid[name]);
    if (errs.length) {
      failures.push(`${name}: canonical invocation rejected -> ${errs.join("; ")}`);
      console.log(`  FAIL  ${name}  ${errs.join("; ")}`);
      continue;
    }

    // 2. Drift self-test: a broken invocation MUST be rejected.
    const driftErrs = validateOrThrow(schema, bad[name]);
    if (driftErrs.length === 0) {
      failures.push(`${name}: drift self-test did not fail — validator would miss real drift`);
      console.log(`  FAIL  ${name}  (drift not detected)`);
      continue;
    }

    console.log(`  PASS  ${name}  (valid ok; drift rejected: ${driftErrs[0]})`);
  }

  // 3. Cross-check: every mock tool the backend implements has a schema (no orphan tools).
  const mockTools = ["patient.get", "utilization.history", "risk_score.get", "protocol.search", "task.create", "audit.write"];
  for (const t of mockTools) {
    if (!(t in schemas)) {
      failures.push(`mock tool '${t}' has no contract schema`);
      console.log(`  FAIL  ${t}  (implemented but no schema)`);
    }
  }

  console.log("");
  if (failures.length) {
    console.error(`MCP contract validation FAILED (${failures.length} issue(s)):`);
    failures.forEach((f) => console.error(` - ${f}`));
    process.exit(1);
  }
  console.log("MCP contract validation PASSED.");
}

main();
