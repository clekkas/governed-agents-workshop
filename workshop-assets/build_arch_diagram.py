"""Generate the workshop solution architecture diagram as an SVG (rendered to PNG separately)."""

import os

W, H = 1560, 1140

TEAL = "#0f766e"
INK = "#0f172a"
SUB = "#475569"
LINE = "#94a3b8"

parts = []


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines=None, fill="#ffffff", border=TEAL, accent=None, dashed=False):
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" '
        f'stroke="{border}" stroke-width="2"{dash}/>'
    )
    if accent:
        parts.append(f'<rect x="{x}" y="{y}" width="7" height="{h}" rx="3" fill="{accent}"/>')
    parts.append(
        f'<text x="{x + 18}" y="{y + 28}" font-family="Segoe UI, Arial" font-size="18" '
        f'font-weight="700" fill="{INK}">{esc(title)}</text>'
    )
    if lines:
        for i, ln in enumerate(lines):
            parts.append(
                f'<text x="{x + 18}" y="{y + 52 + i * 21}" font-family="Segoe UI, Arial" '
                f'font-size="13.5" fill="{SUB}">{esc(ln)}</text>'
            )


def chip_row(x, y, w, chips):
    """Render a row of small pill labels wrapped inside width w."""
    cx = x
    cy = y
    pad = 14
    for c in chips:
        cw = 10 + len(c) * 7.3
        if cx + cw > x + w:
            cx = x
            cy += 34
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{cw:.0f}" height="26" rx="13" fill="#ecfdf5" '
            f'stroke="#99f6e4" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{cx + cw / 2:.0f}" y="{cy + 17}" font-family="Consolas, monospace" '
            f'font-size="12.5" fill="#0f766e" text-anchor="middle">{esc(c)}</text>'
        )
        cx += cw + pad
    return cy + 26


def arrow(x1, y1, x2, y2, label=None, color=LINE, dashed=False, lx=None, ly=None):
    dash = ' stroke-dasharray="6 6"' if dashed else ""
    parts.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.2"'
        f'{dash} marker-end="url(#arrow)"/>'
    )
    if label:
        mx = lx if lx is not None else (x1 + x2) / 2
        my = ly if ly is not None else (y1 + y2) / 2
        tw = 10 + len(label) * 6.6
        parts.append(
            f'<rect x="{mx - tw / 2:.0f}" y="{my - 13:.0f}" width="{tw:.0f}" height="22" rx="6" '
            f'fill="#ffffff" stroke="{LINE}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{mx:.0f}" y="{my + 2:.0f}" font-family="Segoe UI, Arial" font-size="12" '
            f'fill="{SUB}" text-anchor="middle">{esc(label)}</text>'
        )


# ---- canvas ----
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
)
parts.append(
    '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="5" orient="auto">'
    '<path d="M0,0 L10,5 L0,10 z" fill="#64748b"/></marker></defs>'
)
parts.append(f'<rect width="{W}" height="{H}" fill="#f8fafc"/>')

# title
parts.append(
    f'<text x="40" y="46" font-family="Segoe UI, Arial" font-size="26" font-weight="800" '
    f'fill="{TEAL}">Discharge Transition Exception Coordinator — Solution Architecture</text>'
)
parts.append(
    f'<text x="40" y="72" font-family="Segoe UI, Arial" font-size="14.5" fill="{SUB}">'
    'Kaiser Permanente workshop · synthetic data only · every request carries an x-correlation-id</text>'
)

cx_mid = W / 2

# 1. User
box(cx_mid - 190, 96, 380, 52, "Care Manager / ADT Nurse", ["Browser"], fill="#eef2ff", border="#6366f1", accent="#6366f1")

# 2. Frontend
box(120, 186, W - 240, 108, "React UI (Vite)  ·  app/readmission-review-tracker",
    ["Dev server :5173  ·  or built dist served by the backend at :8080"],
    fill="#ffffff", border="#0ea5e9", accent="#0ea5e9")
chip_row(140, 250, W - 280,
         ["Worklist", "Case detail", "Approved risk + provenance", "Evidence (RAG)",
          "Tool & policy calls", "HITL actions + reviewer-name gate", "Backend activity log"])

# 3. Backend
box(120, 340, W - 240, 128, "Node / Express API   :8080",
    ["Serves the built UI  ·  resilient local-orchestrator fallback if the agent service is down"],
    fill="#ffffff", border=TEAL, accent=TEAL)
chip_row(140, 406, W - 280,
         ["GET /api/v1/cases", "POST /api/v1/agent/invoke",
          "/api/v1/tasks  (HITL state machine + audit)", "/api/v1/logs  (activity ring buffer)"])

# 3b. HITL store (right side note under backend)
box(120, 500, 470, 96, "Durable HITL TaskStore",
    ["PendingReview → Approved / NeedsRework / Rejected",
     "policy escalate → Escalated · SLA timeout → Escalated",
     "append-only audit (actor = reviewer name)"],
    fill="#fffbeb", border="#f59e0b", accent="#f59e0b")

# 3c. DTS reference (dashed, graduation target)
box(120, 612, 470, 74, "Durable Task Scheduler reference",
    ["agent-service/orchestrations — wait_for_external_event",
     "+ durable timer → escalate (scales to zero while waiting)"],
    fill="#fffbeb", border="#f59e0b", dashed=True)

# 4. Agent service
box(630, 500, W - 750, 186, "Python FastAPI agent-service   :8081",
    ["Discharge Transition Orchestrator coordinates 7 specialist agents (same invoke contract)"],
    fill="#ffffff", border="#7c3aed", accent="#7c3aed")
chip_row(650, 568, W - 790,
         ["Case Context", "Risk Score", "Evidence Retrieval", "Transition Exception",
          "Care Plan Drafting", "Policy Guardrail", "Human Review"])

# 5. Tools / data / model row
box(120, 726, 430, 164, "MCP tools (mock EHR)",
    ["patient.get            → redact (PHI minimization)",
     "utilization.history    → allow",
     "risk_score.get         → allow (consumed, never generated)",
     "protocol.search        → allow / review_required",
     "task.create            → review_required (draft only)",
     "audit.write            → allow (always)"],
    fill="#f0fdfa", border=TEAL, accent=TEAL)

# RAG domain zone — groups the grounding subsystem (drawn before the box so the box sits on top).
parts.append('<rect x="565" y="698" width="460" height="208" rx="16" fill="#ecfeff" stroke="#0ea5e9" stroke-width="1.6" stroke-dasharray="3 5"/>')
parts.append('<text x="583" y="716" font-family="Segoe UI, Arial" font-size="12.5" font-weight="800" fill="#0ea5e9" letter-spacing="1">RAG DOMAIN (grounding)</text>')

box(580, 726, 430, 164, "RAG KnowledgeBase",
    ["ingest -> retrieve -> ground -> measure",
     "diagnosis-scoped retrieval; claim-level citations",
     "missing protocol -> review_required (escalate)",
     "full view: workshop-assets/rag-domain.svg"],
    fill="#eff6ff", border="#0ea5e9", accent="#0ea5e9")

box(1040, 726, 400, 164, "Microsoft Foundry",
    ["gpt-5-mini deployment (workshop-demo-project)",
     "refine draft wording only — line-count guarded",
     "never adds owners/dates or clinical claims",
     "REST + az token (Win ARM64) or SDK (container)"],
    fill="#faf5ff", border="#7c3aed", accent="#7c3aed")

# safety banner
box(120, 926, W - 240, 62, "Safety boundary (enforced in code)",
    ["Never states a patient is safe to discharge · never alters discharge orders · never makes a clinical "
     "determination · consumes the approved risk score, never generates it · every run stops at the human gate"],
    fill="#fef2f2", border="#dc2626", accent="#dc2626")

# ---- arrows ----
arrow(cx_mid, 148, cx_mid, 186, "renders")
arrow(cx_mid, 294, cx_mid, 340, "HTTPS REST · x-correlation-id")
arrow(cx_mid, 468, cx_mid, 500, None)  # backend -> (down toward stores/agent)
# backend to agent-service
arrow(590, 404, 630, 560, "delegate · AGENT_SERVICE_URL", lx=740, ly=470)
# backend to HITL store
arrow(300, 468, 300, 500, "register / act", )
# HITL store to DTS reference
arrow(355, 596, 355, 612, "graduates to", dashed=True)
# agent-service to tools/data/model
arrow(780, 686, 430, 726, "MCP calls", lx=560, ly=706)
arrow(900, 686, 795, 726, None)
arrow(1080, 686, 1180, 726, "refine draft", lx=1150, ly=706)

parts.append("</svg>")

svg = "\n".join(parts)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture-diagram.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print("wrote", out, len(svg), "bytes")
