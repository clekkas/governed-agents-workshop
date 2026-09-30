"""Generate the MCP + Work IQ deployment diagram (two governed lanes) as SVG.

Reproducible:  python workshop-assets/build_mcp_deployment_diagram.py
Output:        workshop-assets/mcp-workiq-deployment.svg

Shows how the governed clinical tools (our own MCP server) and Work IQ (Microsoft's M365 work-context
service) are deployed and consumed as two SEPARATE lanes under one Entra identity story.
"""

import os

W, H = 1560, 1040

TEAL = "#0f766e"; INK = "#0f172a"; SUB = "#475569"; LINE = "#94a3b8"
AZURE = "#0078d4"; VIOLET = "#7c3aed"; AMBER = "#b45309"; GREEN = "#16a34a"; RED = "#dc2626"
M365 = "#d83b01"

parts = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines=None, fill="#ffffff", border=TEAL, accent=None, dashed=False, tsize=15):
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{border}" stroke-width="2"{dash}/>')
    if accent:
        parts.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>')
    parts.append(f'<text x="{x+18}" y="{y+27}" font-family="Segoe UI, Arial" font-size="{tsize}" font-weight="700" fill="{INK}">{esc(title)}</text>')
    if lines:
        for i, ln in enumerate(lines):
            parts.append(f'<text x="{x+18}" y="{y+51+i*18}" font-family="Segoe UI, Arial" font-size="11.5" fill="{SUB}">{esc(ln)}</text>')


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


def arrow(x1, y1, x2, y2, label=None, color=LINE, dashed=False, width=2.4):
    line(x1, y1, x2, y2, color=color, width=width, dashed=dashed, marker=True)
    if label:
        tag((x1 + x2) / 2, (y1 + y2) / 2, label, color)


# --- canvas ---
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial">')
parts.append('<defs><marker id="arw" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto"><path d="M1,1 L10,5.5 L1,10 Z" fill="#64748b"/></marker></defs>')
parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f8fafc"/>')
parts.append(f'<text x="40" y="46" font-family="Segoe UI, Arial" font-size="24" font-weight="800" fill="{INK}">MCP + Work IQ deployment — two governed lanes, one identity story</text>')
parts.append(f'<text x="40" y="72" font-family="Segoe UI, Arial" font-size="13.5" fill="{SUB}">Clinical / PHI flows through our governed MCP server. M365 work context comes from Work IQ. Synthetic data only.</text>')

# --- Local / dev lane (top) ---
zone(40, 96, 660, 150, "LOCAL / DEV  (zero infra)", TEAL, "#effffb")
box(70, 132, 300, 92, "Agent (in-process tools)", [
    "Default path: governed tools run in-process.",
    "Identical contracts + decisions.",
], accent=TEAL)
box(400, 132, 270, 92, "MCP server — stdio", [
    "python mcp-server/server.py",
    "Subprocess over stdin/stdout.",
], accent=VIOLET, dashed=True)
arrow(370, 178, 400, 178, "stdio", color=VIOLET, dashed=True)

# --- Azure lane ---
zone(40, 300, 900, 700, "AZURE  —  Container App Environment / VNet", AZURE, "#eff6ff")

box(80, 430, 370, 160, "App Container App  (external ingress)", [
    "Backend API + built UI (:8080)",
    "Agent sidecar (:8081) — orchestrator",
    "USE_EXTERNAL_MCP=1 -> hosted MCP",
    "ENABLE_WORKIQ=1 -> M365 context lane",
], accent=AZURE)

box(80, 640, 370, 150, "MCP server Container App", [
    "INTERNAL ingress (private to env / VNet)",
    "streamable-http transport (:8080)",
    "7 governed clinical tools + contracts",
    "Layer 1 secure-MCP: private network",
], accent=VIOLET)

box(500, 430, 400, 160, "Trust plane (shared)", [
    "User-assigned managed identity + RBAC",
    "Key Vault  ·  Azure AI Search (RAG)",
    "App Insights / Log Analytics (tracing)",
    "Durable Task Scheduler (HITL gate)",
], accent=GREEN)

box(500, 640, 400, 150, "Microsoft Foundry", [
    "Foundry account + project",
    "gpt-4o deployment",
    "Hosted agents (orchestrator + specialists)",
], accent=AMBER)

# clinical lane: agent -> MCP server (internal, vertical, clear)
arrow(265, 590, 265, 640, color=VIOLET)
tag(265, 615, "MCP_SERVER_URL (internal https)", VIOLET)

# agent -> trust plane / foundry (managed identity, short horizontal)
arrow(450, 510, 500, 510, "managed identity", color=GREEN)

# --- Microsoft 365 cloud lane (right) ---
zone(1000, 300, 520, 430, "MICROSOFT 365 CLOUD  (Microsoft-hosted — we consume, not host)", M365, "#fff5f0")
box(1030, 360, 460, 150, "Work IQ", [
    "Governed M365 work-context service",
    "MCP / A2A / REST  ·  ~10 generic tools",
    "mail · Teams · files · people · calendar",
    "OPA policy + audit on every call",
], accent=M365)
box(1030, 545, 460, 150, "Identity & governance", [
    "Entra DELEGATED / on-behalf-of ONLY",
    "No app-only auth  ·  no stored secret",
    "Honors user permissions, labels, DLP",
    "Usage-based (Copilot Credits)",
], accent=RED)

# M365 context lane: elbow from App box UP to a clear top corridor, then RIGHT into Work IQ.
# Corridor y=395 is above the trust plane (y=430), so nothing is crossed.
line(300, 430, 300, 395, color=M365, width=2.6)
line(300, 395, 1055, 395, color=M365, width=2.6)
line(1055, 395, 1055, 360, color=M365, width=2.6, marker=True)
tag(675, 395, "Entra OBO (user token, https)", M365)

# --- legend ---
ly0 = 800
parts.append(f'<text x="1000" y="{ly0}" font-family="Segoe UI, Arial" font-size="13" font-weight="800" fill="{INK}">Two lanes, never merged</text>')
line(1000, ly0 + 18, 1040, ly0 + 18, color=VIOLET, width=3)
parts.append(f'<text x="1050" y="{ly0+23}" font-family="Segoe UI, Arial" font-size="12" fill="{SUB}">Clinical / PHI  -&gt;  our governed MCP server (stdio or hosted)</text>')
line(1000, ly0 + 42, 1040, ly0 + 42, color=M365, width=3)
parts.append(f'<text x="1050" y="{ly0+47}" font-family="Segoe UI, Arial" font-size="12" fill="{SUB}">M365 context  -&gt;  Work IQ (Entra OBO, Microsoft-hosted)</text>')

# --- footer note ---
parts.append(f'<text x="40" y="{H-24}" font-family="Segoe UI, Arial" font-size="11.5" fill="{SUB}">Toggles: enable_mcp_server (hosted MCP) · enable_workiq (M365 lane). Off by default; in-process + stdio always work. See mcp-server/README.md and docs/work-iq-overview.md.</text>')

parts.append("</svg>")

out = os.path.join(os.path.dirname(__file__), "mcp-workiq-deployment.svg")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(parts))
print("wrote", out)
