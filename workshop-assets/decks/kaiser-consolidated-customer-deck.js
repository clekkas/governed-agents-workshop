// Consolidated customer presentation deck generator.
//
// One customer-facing deck merging the deck-outline narrative, the reordered 9/29 priorities, and
// the eight source-grounded briefs. Reuses the addendum deck's visual language (theme, helpers).
// Repeatable:  node decks/kaiser-consolidated-customer-deck.js
// Keep text ASCII-safe (no curly quotes / em dashes) so the file validates cleanly.

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.resolve(__dirname, "..", "kaiser-consolidated-customer-deck.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Microsoft";
pptx.company = "Microsoft";
pptx.subject = "Kaiser Permanente - AI Foundry Workshop";
pptx.title = "Kaiser Permanente x Microsoft: Governed Agents on AI Foundry";
pptx.theme = { headFontFace: "Aptos Display", bodyFontFace: "Aptos", lang: "en-US" };

const C = {
  navy: "0B1220", slate: "334155", muted: "64748B", line: "CBD5E1",
  teal: "0F766E", mint: "14B8A6", cyan: "06B6D4", ice: "E6FFFB",
  blue: "2563EB", violet: "7C3AED", amber: "F59E0B", red: "DC2626",
  green: "16A34A", white: "FFFFFF", off: "F8FAFC", card: "FFFFFF",
};

pptx.defineSlideMaster({
  title: "MAIN",
  background: { color: C.off },
  objects: [
    { line: { x: 0, y: 7.16, w: 13.333, h: 0, line: { color: C.teal, width: 1.3 } } },
    { text: { text: "Kaiser Permanente x Microsoft | AI Foundry workshop | Synthetic data only", options: { x: 0.55, y: 7.22, w: 9.5, h: 0.18, fontFace: "Aptos", fontSize: 6.5, color: C.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.55, y: 7.18, color: C.muted, fontFace: "Aptos", fontSize: 7 },
});

function slide(title, kicker) {
  const s = pptx.addSlide("MAIN");
  s.background = { color: C.off };
  if (kicker) s.addText(String(kicker).toUpperCase(), { x: 0.62, y: 0.42, w: 11.8, h: 0.22, fontFace: "Aptos", fontSize: 8, bold: true, color: C.teal, charSpace: 1.2, margin: 0 });
  s.addText(title, { x: 0.6, y: 0.72, w: 12.1, h: 0.55, fontFace: "Aptos Display", fontSize: 23, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  s.addShape(pptx.ShapeType.line, { x: 0.6, y: 1.36, w: 12.1, h: 0, line: { color: C.line, width: 1 } });
  return s;
}
function pill(s, text, x, y, w, color) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.32, rectRadius: 0.08, fill: { color }, line: { color, transparency: 100 } });
  s.addText(text, { x: x + 0.1, y: y + 0.07, w: w - 0.2, h: 0.14, fontFace: "Aptos", fontSize: 7.2, bold: true, color: C.white, align: "center", margin: 0 });
}
function card(s, title, body, x, y, w, h, accent) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: C.card }, line: { color: "E2E8F0", width: 1 }, shadow: { type: "outer", color: "94A3B8", opacity: 0.12, blur: 2, angle: 45, distance: 1 } });
  s.addShape(pptx.ShapeType.rect, { x, y, w: 0.07, h, fill: { color: accent }, line: { color: accent } });
  s.addText(title, { x: x + 0.22, y: y + 0.16, w: w - 0.35, h: 0.24, fontFace: "Aptos", fontSize: 12, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  s.addText(body, { x: x + 0.22, y: y + 0.5, w: w - 0.35, h: h - 0.6, fontFace: "Aptos", fontSize: 9.2, color: C.slate, valign: "top", margin: 0.02, paraSpaceAfterPt: 4, fit: "shrink" });
}
function bullets(s, items, x, y, w, h, opts) {
  opts = opts || {};
  const runs = items.map((it, i) => ({ text: it, options: { bullet: { indent: 12 }, hanging: 3, breakLine: i !== items.length - 1 } }));
  s.addText(runs, { x, y, w, h, fontFace: "Aptos", fontSize: opts.fontSize || 12, color: opts.color || C.slate, margin: 0.03, paraSpaceAfterPt: opts.space || 8, fit: "shrink" });
}
function tell(s, text) {
  s.addText(text, { x: 0.7, y: 6.35, w: 12, h: 0.5, fontFace: "Aptos", fontSize: 10, italic: true, color: C.muted, margin: 0 });
}
function notes(s, t) { s.addNotes(t); }
function divider(kick, title, sub, pills) {
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  pill(s, kick, 0.72, 0.8, 2.8, C.teal);
  s.addText(title, { x: 0.72, y: 1.5, w: 11.6, h: 1.4, fontFace: "Aptos Display", fontSize: 38, bold: true, color: C.white, margin: 0, fit: "shrink" });
  if (sub) s.addText(sub, { x: 0.74, y: 3.0, w: 11.2, h: 0.7, fontFace: "Aptos", fontSize: 15, color: "CBD5E1", margin: 0 });
  (pills || []).forEach((t, i) => pill(s, t, 0.78 + i * 3.5, 4.0, 3.3, [C.amber, C.cyan, C.green, C.violet][i % 4]));
  return s;
}

// ============================================================ 1. Title
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 6.9, w: 13.333, h: 0.12, fill: { color: C.teal }, line: { color: C.teal } });
  pill(s, "AI Foundry workshop", 0.72, 0.9, 3.0, C.teal);
  s.addText("Governed Agents on Microsoft Foundry", { x: 0.72, y: 1.7, w: 11.8, h: 1.6, fontFace: "Aptos Display", fontSize: 40, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("Kaiser Permanente x Microsoft - a two-day, hands-on build of a governed healthcare agent, organized around your priorities.", { x: 0.74, y: 3.5, w: 11.2, h: 0.8, fontFace: "Aptos", fontSize: 16, color: "CBD5E1", margin: 0 });
  ["MCP + Foundry IQ / RAG", "Compliance + guardrails", "Observability + HITL"].forEach((t, i) =>
    pill(s, t, 0.78 + i * 3.6, 4.7, 3.4, [C.cyan, C.amber, C.green][i]));
  s.addText("Synthetic data only. Source-grounded on Microsoft Learn.", { x: 0.78, y: 6.4, w: 10, h: 0.3, fontFace: "Aptos", fontSize: 9, color: "64748B", margin: 0 });
  notes(s, "Open warmly. This is a build workshop, not slideware - we deploy and operate a governed agent together over two days, sequenced around what Kaiser told us matters most.");
}

// ============================================================ 2. Agenda
{
  const s = slide("What we will cover", "Two-day agenda - reordered to your priorities");
  card(s, "Day 1 AM - Tools + grounding", "MCP + Work IQ and Toolboxes, then Foundry IQ / RAG. The new topics you asked to lead with; they overlap on agentic RAG.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Day 1 PM - Safety + placement", "Compliance and guardrails, then Hosted Agents + BYO Registry (tactical, so it comes after the tools and grounding).", 4.75, 1.6, 3.85, 2.0, C.amber);
  card(s, "Day 2 - Earn trust + operate", "LAW / App Insights with dedicated cluster + CMK + AMPLS, HITL / Durable Task Scheduler, then a governance Q&A and roadmap.", 8.8, 1.6, 3.85, 2.0, C.blue);
  bullets(s, [
    "Delivery rhythm each session: concept -> a small live edit -> run it -> reveal the finished checkpoint.",
    "Everything runs on synthetic data; no member data touches the workshop.",
    "Out of scope / futures: BYO Registry sample-only, BYO AKS and SRE agent (roadmap).",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Lead with tools and grounding; then earn the right to trust it with guardrails, observability, and HITL.");
  notes(s, "Walk the two days. Emphasize the reorder: MCP + RAG + toolboxes first per your 9/29 request; hosted agents and BYO registry are tactical and come later.");
}

// ============================================================ 3. Why governed agents
{
  const s = slide("Why governed healthcare agents", "The thesis");
  card(s, "The opportunity", "Agents can triage discharge-transition risk, assemble evidence, and draft plans - compressing manual review while keeping clinicians in control.", 0.7, 1.6, 3.85, 1.95, C.green);
  card(s, "The obligation", "In a regulated setting the agent must never make a clinical determination, expand PHI, or act without a human. Trust is a design requirement, not a feature.", 4.75, 1.6, 3.85, 1.95, C.red);
  card(s, "The approach", "Build the capability and the governance together: grounded retrieval, least-privilege tools, layered guardrails, human approval, and full auditability.", 8.8, 1.6, 3.85, 1.95, C.teal);
  bullets(s, [
    "The agent drafts and explains; a care manager owns every approve / reject decision.",
    "Every material step emits an audit event; the score is consumed, never invented or changed.",
    "Cost and adoption matter: reuse platform resources, do not duplicate spend.",
  ], 0.7, 3.8, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "The whole workshop is an answer to one question: how do we make an agent we can actually trust in production?");
  notes(s, "Frame the two-sided story: capability plus obligation. This sets up why we spend Day 2 on guardrails, observability, and HITL.");
}

// ============================================================ 4. Scenario
{
  const s = slide("The scenario: Discharge Transition Exception Coordinator", "Use case");
  card(s, "The workflow", "A nurse / care manager reviews tomorrow's discharges. The agent estimates transition risk, explains drivers, cites protocol, and flags open transition gaps.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "The human gate", "The agent drafts an exception packet; a care manager approves, requests rework, or rejects. No discharge decision is ever made by the agent.", 4.75, 1.6, 3.85, 2.0, C.amber);
  card(s, "Why this use case", "'Boring is good' - a realistic, high-volume workflow that exercises RAG, MCP tools, hosted agents, guardrails, observability, and HITL end to end.", 8.8, 1.6, 3.85, 2.0, C.violet);
  bullets(s, [
    "Synthetic cases: P0147 (CHF, high), P0221 (COPD, medium), P0310 (pneumonia, critical -> escalates).",
    "Approved risk score is an input the agent consumes; it does not recalculate or override it.",
    "Open gaps: medication reconciliation, follow-up appointment, transportation support.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "One relatable workflow that lets every capability show up in context, not in isolation.");
  notes(s, "Introduce the running example. Everything downstream demos against this. Stress the human gate and that the score is consumed, not invented.");
}

// ============================================================ 5. Safety boundary
{
  const s = slide("Non-negotiable clinical safety boundaries", "Trust boundary");
  card(s, "The agent never...", "makes a clinical determination, says 'safe to discharge', changes the approved risk score, expands PHI, or acts without human approval.", 0.7, 1.6, 3.85, 2.0, C.red);
  card(s, "Enforced in the architecture", "Not just in the prompt: tool scopes, retrieval allowlists, output validation, workflow state, and telemetry all enforce the boundary.", 4.75, 1.6, 3.85, 2.0, C.teal);
  card(s, "Fail closed", "Missing evidence -> disclose and escalate. Illegal transition -> blocked. Agent tries to approve -> denied. Uncertainty routes to a human.", 8.8, 1.6, 3.85, 2.0, C.amber);
  bullets(s, [
    "PHI minimization: tools return redacted / aggregated results by default.",
    "Prohibited-claim detection catches 'safe to discharge' at the output layer.",
    "The score-override case is CRITICAL and must fail-closed in evaluation.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Prompts are necessary but not sufficient - the architecture must enforce the boundary.");
  notes(s, "This is the safety contract. Return to it whenever a participant asks 'but could it...'. The answer is designed-in refusal, not hope.");
}

// ============================================================ 6. Reference architecture
{
  const s = slide("Reference architecture (what we deploy)", "Deployed on Azure + Foundry");
  card(s, "Foundry + agents", "Foundry account + project, gpt-4o deployment, and eight hosted agents (orchestrator + 7 specialists) driving the workflow.", 0.7, 1.6, 3.85, 2.0, C.violet);
  card(s, "App + tools", "Container Apps: a UI/backend plus a Python agent sidecar. MCP tool boundary. Azure AI Search + Storage back RAG / Foundry IQ.", 4.75, 1.6, 3.85, 2.0, C.teal);
  card(s, "Trust plane", "Managed identity + RBAC, Key Vault, App Insights / LAW for tracing, and a Durable Task Scheduler for the human approval gate.", 8.8, 1.6, 3.85, 2.0, C.blue);
  bullets(s, [
    "Keyless CI: GitHub Actions with OIDC, remote Terraform state, human-gated apply.",
    "Everything is IaC (Terraform) and reproducible; synthetic data only.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "A single-tenant, identity-first deployment you can read, redeploy, and reason about.");
  notes(s, "Give the lay of the land before diving into each capability. Point out identity, IaC, and the human gate as first-class, not add-ons.");
}

// ============================================================ Divider: your priorities
divider("Built around your 9/29 priorities", "Your priorities, answered",
  "Eight source-grounded briefs - the questions your team raised, with Microsoft's recommendation for each.",
  ["Secure MCP", "RAG + reuse/cost", "Guardrails + PHI", "Observability + HITL"]);

// ============================================================ 7. MCP + secure MCP
{
  const s = slide("MCP + Work IQ, secured", "Priority - Sarita: the core question");
  card(s, "The tool boundary", "Patient context, protocol search, utilization history, task creation, audit - each a governed MCP tool with a schema contract and a scope.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Securing it (6 layers)", "Private network + dedicated MCP subnet; identity-based auth via project connections; least-privilege RBAC; a Toolbox as one governed endpoint; human approval; always-on audit.", 4.75, 1.6, 3.85, 2.0, C.violet);
  card(s, "Identity over keys", "Prefer managed / agentic identity; user-Entra-token for per-user data; treat static keys as a last resort.", 8.8, 1.6, 3.85, 2.0, C.blue);
  bullets(s, [
    "KP-owned tools over sensitive data should be private, internal-ingress, on their own subnet.",
    "Work IQ is Microsoft's governed M365 context service (next slide) - the agent never bypasses user permissions.",
    "Brief: docs/securing-mcp-servers.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Sarita's core question - a concrete, layered secure-MCP standard your app teams can adopt.");
  notes(s, "Lead the priorities block with secure MCP. Give the six layers, emphasize identity-based auth and the Toolbox as the governed endpoint.");
}

// ============================================================ 7b. Work IQ (M365 work context)
{
  const s = slide("Work IQ: governed M365 work context", "Priority - Sarita/Matt: enterprise context");
  card(s, "What it is", "Microsoft's workplace intelligence layer over Microsoft 365. Reasons over mail, Teams, files, people, calendar, Planner, and enterprise search - with built-in permission-aware governance.", 0.7, 1.6, 3.85, 2.15, C.teal);
  card(s, "How you consume it", "A governed service, not something you build: a remote MCP server (about 10 generic fetch/create/update tools), plus A2A and REST. Point the agent at it.", 4.75, 1.6, 3.85, 2.15, C.violet);
  card(s, "Governed by identity", "Entra delegated / on-behalf-of only (no app-only). User-scoped: honors permissions, sensitivity labels, and DLP; an OPA policy engine and audit run on every call.", 8.8, 1.6, 3.85, 2.15, C.blue);
  bullets(s, [
    "In our design: clinical / PHI data stays on our own governed MCP tools; Work IQ covers the surrounding M365 work context.",
    "Usage-based billing via Copilot Credits, independent of Copilot licensing; governed and cost-managed in the M365 admin center.",
    "Brief: docs/work-iq-overview.md (cites Microsoft Learn).",
  ], 0.7, 4.0, 12.0, 2.1, { fontSize: 11.5 });
  tell(s, "Consume Microsoft's governed M365 context layer - you do not build or secure that server yourself.");
  notes(s, "Reframe from earlier: Work IQ is a shipping, consumable service (MCP/A2A/REST), not just a pattern. Emphasize delegated-identity-only + OPA + audit as the governance story, and the clean split - our MCP for clinical tools, Work IQ for M365 context. Cost is usage-based Copilot Credits.");
}

// ============================================================ 7c. Where the MCP server runs
{
  const s = slide("Where the MCP server runs", "Priority - deployment: two lanes, one identity");
  // Lane A: our governed clinical MCP server (two transports).
  s.addText("CLINICAL / PHI  ->  our governed MCP server", { x: 0.7, y: 1.5, w: 8.0, h: 0.24, fontFace: "Aptos", fontSize: 9, bold: true, color: C.violet, charSpace: 0.6, margin: 0 });
  card(s, "Local / stdio", "python mcp-server/server.py - a stdio subprocess. Zero infra; ships with the app. What you demo in the room.", 0.7, 1.85, 3.85, 1.95, C.violet);
  card(s, "Hosted on Azure", "Same server as a Container App with INTERNAL ingress - private to the environment / VNet (Layer 1 secure MCP). enable_mcp_server=true.", 4.75, 1.85, 3.85, 1.95, C.blue);
  card(s, "Same contracts", "Identical tools, JSON contracts, and decisions either way. Agent routes via USE_EXTERNAL_MCP + MCP_SERVER_URL; in-process stays the default.", 8.8, 1.85, 3.85, 1.95, C.teal);
  // Lane B: Work IQ (consumed, not hosted).
  s.addText("M365 CONTEXT  ->  Work IQ (Microsoft-hosted, we consume)", { x: 0.7, y: 4.1, w: 9.0, h: 0.24, fontFace: "Aptos", fontSize: 9, bold: true, color: C.amber, charSpace: 0.6, margin: 0 });
  card(s, "Separate lane", "Work IQ is not something we deploy - it is Microsoft-hosted. The agent consumes it on the user's Entra on-behalf-of token; no app-only auth, no stored secret.", 0.7, 4.45, 5.9, 1.7, C.amber);
  card(s, "Never merged", "PHI stays on our MCP server; M365 work context comes from Work IQ. Two lanes under one identity - enable_workiq=true, usage-billed via Copilot Credits.", 6.8, 4.45, 5.9, 1.7, C.red);
  tell(s, "Diagram: workshop-assets/mcp-workiq-deployment.svg. Stdio and in-process always work; hosting is a toggle.");
  notes(s, "Answers 'how is the MCP server deployed?'. Same code runs stdio locally or as an internal-ingress Container App on Azure; the internal-ingress IS the private-network layer of secure MCP. Work IQ is the other lane - consumed via Entra OBO, never merged with the clinical PHI tools. Show mcp-workiq-deployment.svg if they want the picture.");
}

// ============================================================ 8. Toolboxes
{
  const s = slide("Toolboxes: one governed endpoint", "Priority - pairs with MCP");
  card(s, "The problem", "Configuring tools + credentials on every agent creates sprawl and drift - hard to govern, version, or rotate.", 0.7, 1.6, 3.85, 1.95, C.amber);
  card(s, "The pattern", "Bundle tools (MCP servers, AI Search, OpenAPI, code interpreter, A2A) into one MCP-compatible Toolbox endpoint with central credentials, versioning, and policy.", 4.75, 1.6, 3.85, 1.95, C.teal);
  card(s, "The payoff", "Point agents at the Toolbox; add / remove / reconfigure tools without changing agent code. Any MCP-capable runtime can consume it.", 8.8, 1.6, 3.85, 1.95, C.green);
  bullets(s, [
    "Centralized authentication, governance, and versioning is the recommended way to run MCP at scale.",
    "One endpoint to secure and audit instead of per-agent credential management.",
    "Reference: Foundry Toolboxes (see securing-mcp-servers.md).",
  ], 0.7, 3.8, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Toolboxes turn 'many tools on many agents' into one governed surface.");
  notes(s, "Natural follow to MCP. The message: govern once, reuse everywhere. This is also where credential rotation and policy live.");
}

// ============================================================ 9. Foundry IQ + RAG
{
  const s = slide("Foundry IQ and RAG done right", "Priority - RAG best practices");
  card(s, "One retrieval endpoint", "Foundry IQ fans out to Blob, AI Search index, Work IQ, SharePoint, Fabric, and MCP - with permission trimming built in.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Evidence before answer", "Retrieve first, build an evidence packet with claim-level citations, then generate. Missing / conflicting evidence -> escalate, never guess.", 4.75, 1.6, 3.85, 2.0, C.violet);
  card(s, "Measure retrieval first", "Use labeled relevance judgments (qrels) to measure precision / recall before tuning prompts or models. Governance and provenance are part of the design.", 8.8, 1.6, 3.85, 2.0, C.blue);
  bullets(s, [
    "Permission-trim with delegated identity (OBO); never rely on a service-identity test for user isolation.",
    "A working local retrieval-eval harness ships in agent-service/eval/.",
    "Briefs: docs/rag-guidance-gpt-rag.md, docs/rag-development-patterns.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "RAG as a production engineering pattern - grounded, measured, and governed, not a demo trick.");
  notes(s, "The RAG core. Emphasize evidence-packet-before-answer and measure-retrieval-first; both are the differentiators from a naive RAG demo.");
}

// ============================================================ 10. Search reuse + cost
{
  const s = slide("Existing vs Foundry Search + capability-host reuse", "Priority - Joshua / Matt: the critical cost question");
  card(s, "Two Search instances", "A: the Search Foundry provisions per project for agent vector stores. B: your existing Search with your RAG indexes. Independent unless you connect them.", 0.7, 1.6, 3.85, 2.0, C.blue);
  card(s, "Reuse to save cost", "Standard setup is bring-your-own: reuse existing or let Foundry provision. The cost win is one always-on Search for both agent and app indexes.", 4.75, 1.6, 3.85, 2.0, C.green);
  card(s, "The caveat", "Capability connections are immutable; build on separate indexes / DBs / containers, never the agent's own. Cosmos / Storage are consumption - little saving.", 8.8, 1.6, 3.85, 2.0, C.red);
  bullets(s, [
    "Reuse only with capacity headroom + isolation + RBAC + accepted lifecycle coupling; else go dedicated.",
    "Usually you do NOT need a second Search - reuse one, isolate, RBAC.",
    "Briefs: docs/capability-host-reuse-and-cost.md, docs/existing-vs-foundry-search.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "The 'do we pay for another Search?' answer: usually no - reuse one, safely.");
  notes(s, "This was the most-raised, critical question. Lead with the two instances, the reuse-for-cost answer, and the immutability caveat.");
}

// ============================================================ 11. SharePoint ingest
{
  const s = slide("SharePoint / O365 docs as a RAG source", "Priority - Matt");
  card(s, "Pattern A - live tool", "Foundry SharePoint tool via the Copilot Retrieval API: per-user OBO honors SharePoint permissions automatically, no pipeline to build.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Pattern B - indexed", "You tokenize / vectorize: crack Office & PDF (Document Intelligence) -> chunk -> embed -> index in AI Search -> ground via Foundry IQ. Full control.", 4.75, 1.6, 3.85, 2.0, C.violet);
  card(s, "The ACL caveat", "The indexed path does NOT auto-honor SharePoint permissions. Restrict the corpus or carry ACLs and security-trim - or use Pattern A.", 8.8, 1.6, 3.85, 2.0, C.red);
  bullets(s, [
    "Choose A for per-user ACLs honored automatically (needs M365 Copilot / PAYG licensing).",
    "Choose B for custom chunking / metadata or a broadly-readable corpus (e.g. approved protocols).",
    "Brief: docs/sharepoint-o365-rag-ingest.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Two KP teams want this - A honors permissions for free, B gives control over tokenization.");
  notes(s, "Matt's ask about SharePoint PDFs/PPT/Word/Excel. Give both patterns and stress the ACL caveat on the indexed path.");
}

// ============================================================ 12. Guardrails + content safety
{
  const s = slide("Compliance, guardrails, and healthcare content safety", "Priority - Sarita");
  card(s, "Layered guardrails", "Input, retrieval, tool, generation, output, and approval - each a separate control. Prompts alone are not enough.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Medical false positives", "General content filters flag benign clinical language (e.g. a Tylenol question). Fix at the right layer - do not weaken safety globally.", 4.75, 1.6, 3.85, 2.0, C.amber);
  card(s, "The fix + the path", "App-side allowlist for clinical terms + a custom content filter on the deployment + a false-positive test suite; ticket the product team for genuine filter errors.", 8.8, 1.6, 3.85, 2.0, C.red);
  bullets(s, [
    "Request, response, and app-side filters are independent knobs - tune the right one.",
    "Keep a healthcare false-positive suite next to the adversarial suite; both gate release.",
    "Brief: docs/healthcare-content-safety.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Never fix a clinical false positive by lowering the global safety bar - tune the layer, encode approved terms.");
  notes(s, "Sarita's content-safety concern. Emphasize layered tuning and the ticket path. Demo a benign clinical prompt passing and 'safe to discharge' still blocked.");
}

// ============================================================ 13. Agent-type decision
{
  const s = slide("Hosted vs prompt vs custom agent", "Priority - Matt: the tipping factor");
  card(s, "Prompt agent", "Instructions + model + tools; Foundry runs it, no code or infra. The fastest path; best without custom orchestration.", 0.7, 1.6, 3.85, 1.95, C.teal);
  card(s, "Hosted agent", "Your code + framework as a container; Foundry gives a managed endpoint, scaling, identity, and tracing. You own the logic.", 4.75, 1.6, 3.85, 1.95, C.violet);
  card(s, "Self-hosted", "Run the agent elsewhere and call the Responses API for Foundry models + tools. Only when you must own the runtime.", 8.8, 1.6, 3.85, 1.95, C.amber);
  bullets(s, [
    "Tipping factors -> hosted: custom orchestration, multi-agent handoffs, an existing framework, or your own code.",
    "Default to a prompt agent; let a real requirement pull you up. Model choice is swappable in all types.",
    "Our multi-agent discharge workflow is exactly the hosted-agent tipping point. Brief: docs/agent-type-decision.md.",
  ], 0.7, 3.75, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Start with prompt; graduate to hosted the moment you need orchestration or your own code.");
  notes(s, "Matt wanted decision criteria. Give the spectrum, the tipping factors, and why our use case is hosted.");
}

// ============================================================ 14. Observability + CMK/AMPLS
{
  const s = slide("Observability, and protecting PHI in logs", "Priority - Lee / Day 2");
  card(s, "See every decision", "One correlation ID joins agents, tools, policy, retrieval, and the human gate. A stable event taxonomy maps to App Insights custom events.", 0.7, 1.6, 3.85, 2.0, C.cyan);
  card(s, "Foundry changes the posture", "Logs can now hold request / response content - possibly PHI. That reclassifies the store from telemetry to regulated data at rest.", 4.75, 1.6, 3.85, 2.0, C.amber);
  card(s, "Dedicated + CMK + AMPLS", "CMK needs a dedicated LAW cluster (double encryption); AMPLS puts ingestion + query on a private endpoint. Plus minimize what you log.", 8.8, 1.6, 3.85, 2.0, C.blue);
  bullets(s, [
    "Sensitive content off by default; pseudonymize actors; never capture secrets.",
    "Start with the Foundry workspace on the dedicated cluster; KP volume makes it cost-favorable.",
    "Brief: docs/observability-dedicated-cluster-cmk-ampls.md (Lee leads Day 2).",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Minimize at the source, CMK-encrypt what remains, keep it on the private network.");
  notes(s, "Two-in-one: the correlation-trace story plus the PHI-protection posture. The driver is request/response content in Foundry logs.");
}

// ============================================================ 15. HITL / DTS
{
  const s = slide("Human in the loop: the durable approval gate", "Priority - Day 2");
  card(s, "The gate", "Every run drafts an exception packet, then STOPS at a care-manager approval gate. The agent drafts and reworks only; a human owns approve / reject.", 0.7, 1.6, 3.85, 2.0, C.amber);
  card(s, "Durable + auditable", "PendingReview -> Approved / NeedsRework / Rejected; SLA timeout or policy -> Escalated. Every transition writes an append-only audit record.", 4.75, 1.6, 3.85, 2.0, C.teal);
  card(s, "Scales to zero waiting", "On the Durable Task Scheduler the run pauses on an external event + durable timer - a review can safely take hours or days, consuming no compute.", 8.8, 1.6, 3.85, 2.0, C.violet);
  bullets(s, [
    "Guardrails in code: illegal transition -> 409; an agent trying to approve -> 403.",
    "Live and verified end to end in the deployed app against the real Durable Task Scheduler.",
    "Brief / doc: docs/hitl-durable-task-scheduler.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "A governed workflow must pause for a human - durably, with an audit trail.");
  notes(s, "The human-control capstone. This is built and running today; demo approve, a blocked illegal transition, and SLA auto-escalation.");
}

// ============================================================ Divider: prove + plan
divider("Earn the right to trust it", "Prove it, then pilot it",
  "End-to-end, gated by evaluation, with a staged path to production.",
  ["End-to-end run", "Evaluation gate", "30/60/90 roadmap"]);

// ============================================================ 16. End-to-end
{
  const s = slide("The whole thing, working end to end", "Playback");
  card(s, "One case, all layers", "Invoke a discharge case: eight agents hand off, tools are scoped and redacted, RAG cites protocol, guardrails hold, and it stops at the human gate.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "One trace", "Copy the correlation ID and walk the ordered events - tool decisions, agent handoffs, policy calls, the review transition - one join key across the run.", 4.75, 1.6, 3.85, 2.0, C.cyan);
  card(s, "One decision", "A care manager approves in the UI; the durable task reaches Approved with a full audit trail. An agent-actor approve is denied.", 8.8, 1.6, 3.85, 2.0, C.amber);
  bullets(s, [
    "This is the deployed system, not a mockup - live on Azure Container Apps + Foundry.",
    "The same contract runs in foundry mode (hosted agents) and a local mode for offline demos.",
    "Reference: docs/observability-correlation-trace.md, docs/hitl-durable-task-scheduler.md.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Capability and governance in one run - the point of the whole two days.");
  notes(s, "The integrated demo. Run one case start to finish; let the trace and the human gate tell the story.");
}

// ============================================================ 17. Evaluation gate
{
  const s = slide("Evaluation as a release gate", "Prove it is safe");
  card(s, "Golden cases", "What it must do well: cite grounded evidence, disclose missing info, consume the approved score, route to human review.", 0.7, 1.6, 3.85, 1.9, C.green);
  card(s, "Adversarial cases", "What it must refuse: say 'safe to discharge', expand PHI, or recalculate / lower the risk score. Score-override is CRITICAL and must fail-closed.", 4.75, 1.6, 3.85, 1.9, C.red);
  card(s, "A real gate", "Deterministic, offline checks over synthetic cases; a failure returns non-zero and blocks the release. Not a vibe check.", 8.8, 1.6, 3.85, 1.9, C.teal);
  bullets(s, [
    "Measure retrieval with qrels; assert safety gates on the structured result before any pilot.",
    "Datasets: evaluation/golden-cases.jsonl and evaluation/adversarial-cases.jsonl.",
    "Demo: green -> inject a break -> red / gate-blocked -> revert -> green (no code editing).",
  ], 0.7, 3.75, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "You do not pilot a healthcare agent on trust - you pilot it on a passing gate.");
  notes(s, "Show that safety is testable and enforced in CI. The score-override adversarial case is the one to highlight.");
}

// ============================================================ 18. Roadmap
{
  const s = slide("30 / 60 / 90-day pilot roadmap", "What Kaiser does next");
  card(s, "0 - 30 days", "Stand up the governed pattern on a synthetic corpus; wire Foundry IQ to approved protocols; agree the safety gate and telemetry taxonomy.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "30 - 60 days", "Secure MCP + Toolbox for the first real tools; dedicated LAW cluster + CMK + AMPLS; capability-host reuse decisions per app team.", 4.75, 1.6, 3.85, 2.0, C.blue);
  card(s, "60 - 90 days", "Limited pilot behind the human gate with a real (governed) source; continuous evaluation; expand toolboxes and observability dashboards.", 8.8, 1.6, 3.85, 2.0, C.violet);
  bullets(s, [
    "Cost discipline throughout: reuse platform resources; commitment-tier logging; no duplicated Search.",
    "Governance owners named per control (guardrails, RBAC, content safety, HITL).",
    "Futures to scope: BYO Registry, BYO AKS for hosted agents, SRE agent - as separate tracks.",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "A staged path: prove the pattern, harden the platform, then pilot behind the human gate.");
  notes(s, "Close with a concrete, cost-aware plan. Tie each phase back to the priorities and the two-quarter window Kaiser cares about.");
}

// ============================================================ 19. Deeper reading
{
  const s = slide("Where to go deeper", "Source-grounded briefs");
  card(s, "Tools + grounding", "Securing MCP tool servers; reusing capability-host Search and its cost; existing vs. Foundry search; SharePoint / O365 RAG ingest; RAG design guidance.", 0.7, 1.6, 5.9, 1.9, C.teal);
  card(s, "Safety + agents", "Healthcare content safety; choosing the right agent type; governance, security and observability; guardrail policy and its test matrix.", 6.8, 1.6, 5.9, 1.9, C.violet);
  card(s, "Operate", "Dedicated cluster with CMK and AMPLS; end-to-end trace correlation; human-in-the-loop with the Durable Task Scheduler.", 0.7, 3.65, 5.9, 1.7, C.blue);
  card(s, "Run the workshop", "Two-day agenda, run-of-show, and a facilitator cheat-sheet that maps each stakeholder question to the right brief.", 6.8, 3.65, 5.9, 1.7, C.amber);
  tell(s, "Detailed, source-grounded briefs are provided as a leave-behind pack; every brief cites current Microsoft Learn.");
  notes(s, "Leave-behind slide. Point each persona to their briefs; the facilitator cheat-sheet has the full question -> doc lookup.");
}

// ============================================================ Close
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  pill(s, "Thank you", 0.72, 0.9, 2.2, C.teal);
  s.addText("Capability and governance, built together.", { x: 0.72, y: 1.8, w: 11.6, h: 1.4, fontFace: "Aptos Display", fontSize: 34, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("Two days: build a governed discharge-transition agent, prove it with an evaluation gate, and leave with a cost-aware pilot roadmap.", { x: 0.74, y: 3.2, w: 11.0, h: 0.9, fontFace: "Aptos", fontSize: 15, color: "CBD5E1", margin: 0 });
  ["Grounded on Microsoft Learn", "Synthetic data only", "Your priorities first"].forEach((t, i) =>
    pill(s, t, 0.78 + i * 3.7, 4.5, 3.5, [C.cyan, C.green, C.amber][i]));
  notes(s, "Close on the through-line: we do not choose between capability and governance - we build them together, sequenced around what Kaiser asked for.");
}

pptx.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
