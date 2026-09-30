"""Generate the RAG domain / pipeline diagram as SVG.

Reproducible:  python workshop-assets/build_rag_domain_diagram.py
Output:        workshop-assets/rag-domain.svg

Shows the retrieval-augmented-generation domain as a bounded space with a left-to-right pipeline
(Sources -> Ingest -> Retrieve -> Ground -> Measure) and the local-stub -> Foundry IQ / Azure AI
Search graduation, all under one 'same retrieval contract'. Grounded in
agent-service/src/discharge_transition_agent/knowledge.py, data/rag-docs, and the eval harness.
"""

import os

W, H = 1640, 1040

TEAL = "#0f766e"; INK = "#0f172a"; SUB = "#475569"; LINE = "#94a3b8"
AZURE = "#0ea5e9"; VIOLET = "#7c3aed"; AMBER = "#b45309"; GREEN = "#16a34a"; RED = "#dc2626"
BLUE = "#2563eb"

parts = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines=None, fill="#ffffff", border=TEAL, accent=None, dashed=False, tsize=14):
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{border}" stroke-width="2"{dash}/>')
    if accent:
        parts.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>')
    parts.append(f'<text x="{x+16}" y="{y+25}" font-family="Segoe UI, Arial" font-size="{tsize}" font-weight="700" fill="{INK}">{esc(title)}</text>')
    if lines:
        for i, ln in enumerate(lines):
            parts.append(f'<text x="{x+16}" y="{y+47+i*17}" font-family="Segoe UI, Arial" font-size="11" fill="{SUB}">{esc(ln)}</text>')


def zone(x, y, w, h, label, color, fill):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{color}" stroke-width="1.8" stroke-dasharray="3 5"/>')
    parts.append(f'<text x="{x+18}" y="{y+26}" font-family="Segoe UI, Arial" font-size="13" font-weight="800" fill="{color}" letter-spacing="1">{esc(label)}</text>')


def line(x1, y1, x2, y2, color=LINE, width=2.4, dashed=False, marker=False):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    m = ' marker-end="url(#arw)"' if marker else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash}{m}/>')


def tag(x, y, label, color=SUB):
    tw = 9 + len(label) * 6.3
    parts.append(f'<rect x="{x-tw/2:.0f}" y="{y-13:.0f}" width="{tw:.0f}" height="22" rx="6" fill="#ffffff" stroke="{color}" stroke-width="1"/>')
    parts.append(f'<text x="{x:.0f}" y="{y+2:.0f}" font-family="Segoe UI, Arial" font-size="11" fill="{SUB}" text-anchor="middle">{esc(label)}</text>')


def arrow(x1, y1, x2, y2, label=None, color=LINE, dashed=False, width=2.6):
    line(x1, y1, x2, y2, color=color, width=width, dashed=dashed, marker=True)
    if label:
        tag((x1 + x2) / 2, (y1 + y2) / 2, label, color)


# --- canvas ---
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial">')
parts.append('<defs><marker id="arw" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto"><path d="M1,1 L10,5.5 L1,10 Z" fill="#64748b"/></marker></defs>')
parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f8fafc"/>')
parts.append(f'<text x="40" y="46" font-family="Segoe UI, Arial" font-size="24" font-weight="800" fill="{INK}">RAG domain — grounding the discharge-transition agent</text>')
parts.append(f'<text x="40" y="72" font-family="Segoe UI, Arial" font-size="13.5" fill="{SUB}">Sources to cited answer, with missing-evidence escalation and measured retrieval. Local KnowledgeBase today; Foundry IQ / Azure AI Search tomorrow — same retrieval contract. Synthetic data only.</text>')

# --- RAG domain zone (the pipeline) ---
zone(40, 100, 1560, 560, "RAG DOMAIN  (query -> cited evidence + coverage signal)", TEAL, "#f0fdfa")

# Pipeline columns
colw, coly, colh = 280, 170, 300
xs = [70, 380, 690, 1000, 1310]

box(xs[0], coly, colw, colh, "1 · Sources", [
    "data/rag-docs (effective-dated):",
    " CHF / readmission protocols,",
    " med-rec, escalation, care SOP",
    "SharePoint / O365 (future):",
    " PDF · PPT · Word · Excel",
    "each carries ACLs + labels",
], accent=AMBER)

box(xs[1], coly, colw, colh, "2 · Ingest", [
    "extract text",
    "chunk",
    "embed",
    "index",
    "ACL-trimmed at index time",
    "(permissions honored)",
], accent=AZURE)

box(xs[2], coly, colw, colh, "3 · Retrieve", [
    "build query from the case",
    "diagnosis-scoping filter:",
    " specialty doc only for its dx",
    " (CHF never surfaces for COPD)",
    "top-k + score boost",
    "confidence band (High/Med/Low)",
], accent=BLUE)

box(xs[3], coly, colw, colh, "4 · Ground", [
    "evidence packet BEFORE answer",
    "claim-level citations",
    " (best-sentence + source file)",
    "missing specialty protocol ->",
    " review_required -> HITL",
    "escalate, never guess",
], accent=VIOLET)

box(xs[4], coly, colw, colh, "5 · Measure", [
    "retrieval eval harness",
    "precision@k · recall@k · MRR",
    "qrels.jsonl (tune / held_out)",
    "gate: min precision@k",
    "measure BEFORE you tune",
    "(GPT-RAG accelerator pattern)",
], accent=GREEN)

# pipeline arrows
for i in range(4):
    ax = xs[i] + colw
    arrow(ax, coly + colh / 2, xs[i + 1], coly + colh / 2, color=TEAL)

# escalation callout from Ground down to HITL (outside the happy path)
line(xs[3] + colw / 2, coly + colh, xs[3] + colw / 2, 700, color=VIOLET, width=2.6, dashed=True, marker=True)

# --- Two-lane graduation (below the domain) ---
zone(40, 700, 1090, 280, "SAME RETRIEVAL CONTRACT  —  swap the backend, keep qrels + metrics", INK, "#ffffff")
box(70, 740, 500, 210, "Today — local KnowledgeBase", [
    "agent-service/.../knowledge.py",
    "keyword scoring over data/rag-docs",
    "diagnosis-scoped, cited, offline & deterministic",
    "same query -> cited evidence contract",
    "no cloud, no vector store to manage",
], accent=TEAL)
box(600, 740, 500, 210, "Graduation — Foundry IQ / Azure AI Search", [
    "swap the retriever; agents unchanged",
    "existing vs Foundry search (docs/existing-vs-foundry-search.md)",
    "capability-host reuse + cost:",
    " one always-on Search for agent + app indexes",
    " build on SEPARATE indexes (immutable connections)",
], accent=AZURE)
arrow(570, 845, 600, 845, "same contract", color=INK)

# HITL target box (right of graduation)
box(1160, 740, 440, 210, "Human review gate (HITL)", [
    "missing / low-coverage evidence ->",
    "review_required -> care-manager approval",
    "Durable Task Scheduler (SLA + escalate)",
    "the agent drafts + cites; a human decides",
    "nothing proceeds on ungrounded evidence",
], accent=RED)
tag(xs[3] + colw / 2, 700, "review_required", VIOLET)

# --- footer ---
parts.append(f'<text x="40" y="{H-22}" font-family="Segoe UI, Arial" font-size="11.5" fill="{SUB}">Grounded in knowledge.py (retrieve / diagnosis-scoping / has_protocol_for), data/rag-docs, and agent-service/eval. See docs/rag-guidance-gpt-rag.md, existing-vs-foundry-search.md, capability-host-reuse-and-cost.md.</text>')

parts.append("</svg>")

out = os.path.join(os.path.dirname(__file__), "rag-domain.svg")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(parts))
print("wrote", out)
