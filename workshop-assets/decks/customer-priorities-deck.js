// Customer-priorities deck generator - one slide per priority brief from the 9/29 KP planning call.
//
// Repeatable:  node decks/customer-priorities-deck.js
// Reuses the build-addendum deck's visual language (theme, helpers) for a consistent look.
// Keep text ASCII-safe (no curly quotes / em dashes) so the file validates cleanly.

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.resolve(__dirname, "..", "kaiser-customer-priorities-briefs.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Microsoft Scout";
pptx.company = "Microsoft";
pptx.subject = "Kaiser Permanente - Customer Priority Briefs";
pptx.title = "Kaiser Workshop: Customer Priority Briefs";
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
    { text: { text: "Kaiser Permanente | Customer priority briefs (9/29 call) | Synthetic data only", options: { x: 0.55, y: 7.22, w: 9.5, h: 0.18, fontFace: "Aptos", fontSize: 6.5, color: C.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.55, y: 7.18, color: C.muted, fontFace: "Aptos", fontSize: 7 },
});

function slide(title, kicker) {
  const s = pptx.addSlide("MAIN");
  s.background = { color: C.off };
  if (kicker) s.addText(String(kicker).toUpperCase(), { x: 0.62, y: 0.42, w: 11.5, h: 0.22, fontFace: "Aptos", fontSize: 8, bold: true, color: C.teal, charSpace: 1.2, margin: 0 });
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

// ---------- Section divider ----------
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  pill(s, "Customer-informed", 0.72, 0.8, 2.6, C.teal);
  s.addText("Customer priority briefs", { x: 0.72, y: 1.5, w: 11.5, h: 0.9, fontFace: "Aptos Display", fontSize: 40, bold: true, color: C.white, margin: 0 });
  s.addText("What Kaiser asked for on the 9/29 planning call - one source-grounded brief per priority.", { x: 0.74, y: 2.6, w: 11, h: 0.5, fontFace: "Aptos", fontSize: 15, color: "CBD5E1", margin: 0 });
  ["Capability-host reuse + cost", "Secure MCP", "CMK / AMPLS for PHI"].forEach((t, i) =>
    pill(s, t, 0.78 + i * 3.5, 3.5, 3.3, [C.amber, C.cyan, C.green][i]));
  s.addText("Each brief cites current Microsoft Learn. Synthetic data only.", { x: 0.78, y: 6.8, w: 10, h: 0.3, fontFace: "Aptos", fontSize: 9, color: "64748B", margin: 0 });
  notes(s, "These slides answer the specific asks Kaiser raised on the 9/29 call, in their reprioritized order. Open the matching docs/*.md brief live for depth.");
}

// ---------- Agenda reordering ----------
{
  const s = slide("Agenda reordered to the customer's priority", "Sequence - per the 9/29 call");
  card(s, "Day 1 morning (lead)", "MCP + Work IQ + Toolboxes, then Foundry IQ / RAG. The 'fresh, new' topics the customer wanted first; the three overlap on agentic RAG.", 0.7, 1.6, 3.85, 1.9, C.teal);
  card(s, "Day 1 afternoon", "Compliance / guardrails, then Hosted Agents + BYO Registry - demoted to 'tactical, later' per the customer.", 4.75, 1.6, 3.85, 1.9, C.amber);
  card(s, "Day 2", "LAW / App Insights (+ dedicated cluster / CMK / AMPLS), HITL / Data Task Scheduler, then a governance Q&A + roadmap.", 8.8, 1.6, 3.85, 1.9, C.blue);
  bullets(s, [
    "Chapter numbers stay stable as topic tags; only the delivery order changed (decks/checkpoints unaffected).",
    "Toolboxes pulled forward to pair with MCP; hosted agents + BYO registry moved to the afternoon.",
    "Source: workshop-assets/agenda-2-day.md + run-of-show.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "Lead with tools + grounding; earn trust (guardrails, observability, HITL) after the build.");
  notes(s, "Set the frame: we reorganized the two days around what Kaiser said mattered most - MCP, RAG, toolboxes first; hosted agents and BYO registry are tactical and come later.");
}

// ---------- Capability-host reuse + cost ----------
{
  const s = slide("Capability-host reuse + cost - the critical question", "Priority - Matt / Sarita");
  card(s, "The question", "Can app teams reuse the AI Search / Cosmos / Storage Foundry provisions per project, or must they pay for their own? Framed as cost - app teams pay from their own budgets.", 0.7, 1.6, 3.85, 2.0, C.amber);
  card(s, "The answer", "Standard setup is BYO: create new OR pass existing resource IDs. Reuse is a first-class path. The real cost win is one always-on AI Search reused for agent vector stores AND app RAG indexes.", 4.75, 1.6, 3.85, 2.0, C.green);
  card(s, "The caveat", "Capability connections are immutable; changing a project's resources means recreating the project. Build on SEPARATE indexes / DBs / containers, never the agent's own.", 8.8, 1.6, 3.85, 2.0, C.red);
  bullets(s, [
    "Search = base-rate, always-on -> the cost-optimization move. Cosmos / Storage = consumption -> little saving.",
    "Reuse only with capacity headroom + logical isolation + RBAC + accepted lifecycle coupling; else go dedicated.",
    "Brief: docs/capability-host-reuse-and-cost.md (grounded in standard-agent-setup on Microsoft Learn).",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "What to tell app teams: usually you do NOT need a second Search - reuse one, isolate, RBAC.");
  notes(s, "This was the most-raised, 'critical' question. Lead with: yes you can reuse (BYO), the money is in Search, and the immutability caveat. Open the brief for the per-resource table.");
}

// ---------- Securing MCP servers ----------
{
  const s = slide("Securing MCP servers - the core question", "Priority - Sarita");
  card(s, "Network", "Private MCP on Azure Container Apps internal ingress + a dedicated MCP subnet. Public endpoints only for trusted read-only servers.", 0.7, 1.6, 3.85, 1.9, C.blue);
  card(s, "Identity auth", "Via a Foundry project connection: prefer project-managed-identity / agentic-identity; user-entra-token for per-user data. Static custom-keys are a last resort.", 4.75, 1.6, 3.85, 1.9, C.teal);
  card(s, "Govern + control", "Least-privilege tool contracts + RBAC; a Toolbox as one governed endpoint (central creds / versioning / policy); human approval on write tools; always-on audit.", 8.8, 1.6, 3.85, 1.9, C.violet);
  bullets(s, [
    "Six layers, no single control is sufficient: network, auth, authorization, centralize, human approval, audit.",
    "Toolbox is the recommended way to run MCP at scale - one MCP-compatible endpoint instead of per-agent creds.",
    "Brief: docs/securing-mcp-servers.md (grounded in Foundry MCP + toolbox + network-isolation docs).",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "For KP-owned tools over sensitive data: private + managed identity + toolbox + approval + audit.");
  notes(s, "Sarita called this a 'core question'. Give the six layers, emphasize identity-based auth over keys and the Toolbox as the governed endpoint. Tie human approval back to the HITL gate.");
}

// ---------- Existing vs Foundry Search ----------
{
  const s = slide("Existing AI Search vs Foundry capability-host Search", "Priority - Joshua");
  card(s, "Two instances", "A: the Search Foundry provisions per project for the agent's vector stores. B: your existing Search with your app RAG indexes. Independent unless you connect them.", 0.7, 1.6, 3.85, 1.9, C.blue);
  card(s, "How to connect", "BYO your existing Search as the capability host (pass its resource ID), OR ground on your index via a Foundry IQ 'searchIndex' knowledge source - keep your ingestion pipeline.", 4.75, 1.6, 3.85, 1.9, C.teal);
  card(s, "Which to use", "Foundry IQ as the one retrieval endpoint for new / multi-source builds; AI Search direct for an existing single-index pipeline or rollback.", 8.8, 1.6, 3.85, 1.9, C.violet);
  bullets(s, [
    "Do not reflexively stand up a third Search - reuse one service, or BYO the existing one.",
    "Cost lever is the same as capability-host reuse: one always-on Search, app + agent indexes, RBAC-isolated.",
    "Brief: docs/existing-vs-foundry-search.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "They are independent Azure resources; connect deliberately, reuse for cost.");
  notes(s, "Joshua's concern: the capability-host Search is separate from their existing one. Clarify the two, the two connect patterns, and the reuse/cost pointer.");
}

// ---------- Hosted vs prompt vs custom agent ----------
{
  const s = slide("Hosted vs prompt vs custom agent - the tipping factor", "Priority - Matt");
  card(s, "Prompt agent", "Instructions + model + tools; Foundry runs it, no code/infra. Fastest path. Best for internal tools and agents without custom orchestration.", 0.7, 1.6, 3.85, 1.9, C.teal);
  card(s, "Hosted agent", "Your code + framework (Agent Framework, LangGraph, etc.) as a container; Foundry gives managed endpoint, scaling, identity, tracing. You own the logic.", 4.75, 1.6, 3.85, 1.9, C.violet);
  card(s, "Self-hosted", "Run the agent elsewhere and call the Responses API for Foundry models + tools. Only when you must own the runtime / environment.", 8.8, 1.6, 3.85, 1.9, C.amber);
  bullets(s, [
    "Tipping factors -> hosted: custom orchestration, multi-agent handoffs, an existing framework, or your own code.",
    "Default to prompt agent; let a real requirement pull you up to hosted. Model choice is swappable in all types.",
    "The discharge use case is multi-agent + custom control flow -> hosted. Brief: docs/agent-type-decision.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "Start with prompt; graduate to hosted the moment you need orchestration or your own code.");
  notes(s, "Matt wanted the decision criteria. Give the spectrum, the tipping factors, and why our use case is hosted. Show a prompt agent vs the hosted multi-agent live if time allows.");
}

// ---------- Healthcare content safety ----------
{
  const s = slide("Healthcare content safety - fixing medical false positives", "Priority - Sarita");
  card(s, "Why it happens", "Content Safety models are general-purpose, not healthcare-tuned. Benign clinical language (e.g. a Tylenol question) can trip generic harm categories.", 0.7, 1.6, 3.85, 1.9, C.red);
  card(s, "Layered fix", "Do not globally weaken the filter. Tune per layer: input filter thresholds, app-side allowlist for clinical terms, a custom content filter on the deployment, groundedness, post-filter, HITL.", 4.75, 1.6, 3.85, 1.9, C.teal);
  card(s, "When still wrong", "Reproduce with category + severity, apply mitigations, then open a product-team ticket. Models update monthly - track the fix and add a false-positive test so it can't regress.", 8.8, 1.6, 3.85, 1.9, C.amber);
  bullets(s, [
    "Request, response, and app-side filters are separate knobs - fix false positives at the right layer.",
    "Keep a healthcare false-positive suite next to the adversarial suite; both gate release.",
    "Brief: docs/healthcare-content-safety.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "Never fix a clinical false positive by lowering safety globally - tune the layer and encode approved terms.");
  notes(s, "Sarita's concern about content filters flagging legitimate medical questions. Emphasize layered tuning and the ticket path; do not lower the global bar.");
}

// ---------- Dedicated LAW + CMK + AMPLS ----------
{
  const s = slide("Protecting PHI in logs - dedicated cluster + CMK + AMPLS", "Priority - Lee / Day 2");
  card(s, "Why now", "Foundry logs can hold request/response content - possibly PHI. That reclassifies the log store from telemetry to regulated data at rest.", 0.7, 1.6, 3.85, 1.9, C.red);
  card(s, "The controls", "CMK requires a dedicated LAW cluster (>= 100 GB/day commitment, double encryption). AMPLS puts ingestion + query on a private endpoint, off the public internet.", 4.75, 1.6, 3.85, 1.9, C.teal);
  card(s, "Plus minimize", "CMK/AMPLS protect the store; still minimize what you log - sensitive content off by default, pseudonymize actors, never capture secrets.", 8.8, 1.6, 3.85, 1.9, C.blue);
  bullets(s, [
    "Start with the Foundry workspace on the dedicated cluster; expand later. KP volume makes it cost-neutral-to-favorable.",
    "Sequence: Key Vault + CMK -> dedicated cluster + MI -> link workspace -> AMPLS + private DNS -> validate.",
    "Brief: docs/observability-dedicated-cluster-cmk-ampls.md (grounded in Azure Monitor Learn).",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  tell(s, "Minimize at the source, CMK-encrypt what remains, keep it on the private network. Lee leads Day 2.");
  notes(s, "The driver is PHI in Foundry request/response. Give the three controls and the fact that CMK needs a dedicated cluster. Bring real cost numbers with Lee.");
}

// ---------- SharePoint / O365 RAG ingest ----------
{
  const s = slide("SharePoint / O365 docs as a RAG source", "Priority - Matt");
  card(s, "Pattern A - live tool", "Foundry SharePoint tool via the Copilot Retrieval API: per-user OBO honors SharePoint ACLs, no pipeline to build. Needs M365 Copilot / PAYG; same tenant; one per agent.", 0.7, 1.6, 3.85, 2.0, C.teal);
  card(s, "Pattern B - indexed", "You tokenize/vectorize: crack Office/PDF (Document Intelligence) -> chunk -> embed (integrated vectorization) -> index in AI Search -> ground via Foundry IQ. Full control; app-only ACL.", 4.75, 1.6, 3.85, 2.0, C.violet);
  card(s, "Choose", "Need per-user ACLs auto-honored + Copilot licensing -> A. Need custom chunking/metadata or a broadly-readable corpus -> B. Either way: cite, escalate on missing evidence, govern the source.", 8.8, 1.6, 3.85, 2.0, C.amber);
  bullets(s, [
    "Indexed path does NOT auto-honor SharePoint permissions - restrict the corpus or carry ACLs and security-trim.",
    "Test allowed AND denied users; a service-identity test does not prove user isolation.",
    "Brief: docs/sharepoint-o365-rag-ingest.md (grounded in Foundry SharePoint tool + AI Search docs).",
  ], 0.7, 3.85, 12.0, 2.2, { fontSize: 11.5 });
  tell(s, "Two KP teams want this - pick A for ACLs-honored, B for control over tokenization.");
  notes(s, "Matt asked about tokenizing SharePoint PDFs/PPT/Word/Excel. Give both patterns and the ACL caveat for the indexed path.");
}

// ---------- Attendee -> brief map ----------
{
  const s = slide("Who wants what - attendee to brief map", "Facilitator reference");
  card(s, "Sarita (program lead)", "Cost not duplicated, secure MCP, content-safety confidence. -> capability-host-reuse-and-cost, securing-mcp-servers, healthcare-content-safety.", 0.7, 1.6, 5.9, 1.7, C.teal);
  card(s, "Matt (platform architect)", "Capability-host reuse + cost, hosted-vs-prompt tipping factor, SharePoint RAG. -> capability-host-reuse-and-cost, agent-type-decision, sharepoint-o365-rag-ingest.", 6.8, 1.6, 5.9, 1.7, C.violet);
  card(s, "Joshua (platform engineer)", "Existing vs Foundry Search, verify RAG pattern. -> existing-vs-foundry-search, rag-guidance-gpt-rag.", 0.7, 3.45, 5.9, 1.7, C.blue);
  card(s, "Lee (observability, Day 2)", "Dedicated cluster + CMK + AMPLS for PHI logs. -> observability-dedicated-cluster-cmk-ampls.", 6.8, 3.45, 5.9, 1.7, C.amber);
  tell(s, "Full lookup + the three memorize-these answers: workshop-assets/facilitator-cheatsheet.md.");
  notes(s, "Steer each question to the right person and open the matching brief live. The cheat-sheet has the full question->doc lookup.");
}

pptx.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
