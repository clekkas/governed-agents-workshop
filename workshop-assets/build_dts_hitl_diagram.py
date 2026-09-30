"""Generate the Discharge-transition HITL / Durable Task Scheduler architecture diagram as SVG.

Reproducible:  python workshop-assets/build_dts_hitl_diagram.py
Output:        workshop-assets/dts-hitl-architecture.svg

Azure-style architecture diagram (light-blue zone, rounded cards with icon glyphs, colored workflow
arrows, status chips, operations/security band, legend) for the workshop's human-in-the-loop review
gate on the Durable Task Scheduler. Grounded in agent-service/orchestrations/function_app.py
(wait_for_external_event('ReviewDecision') raced with a durable SLA timer), hitl_dts.py, and the
backend /api/v1/tasks action API. Synthetic data only; the DTS path is the graduation reference.

Icons are simplified glyphs in the Azure palette (not the official trademarked product icons); drop
in the official Azure icon set if desired.
"""

import os

W, H = 2000, 1150

# palette
INK = "#0f172a"; SUB = "#475569"; MUT = "#64748b"
AZ = "#0078d4"; BLUE = "#2563eb"; SKY = "#0ea5e9"
AMBER = "#f0a500"; AMBTX = "#b45309"; GREEN = "#16a34a"; RED = "#dc2626"; VIOLET = "#7c3aed"
ZONE = "#eaf3fc"; ZONE_BD = "#bcd8f5"; CARD = "#ffffff"; INNER = "#f5f9ff"; DTSBOX = "#dcebfb"
LINE = "#94a3b8"

p = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rrect(x, y, w, h, r, fill, stroke=None, sw=2, dash=None, shadow=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    fl = ' filter="url(#sh)"' if shadow else ""
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}{d}{fl}/>')


def txt(x, y, s, size=14, color=INK, bold=False, anchor="start", mono=False, italic=False):
    fam = "Consolas, monospace" if mono else "Segoe UI, Arial"
    b = ' font-weight="700"' if bold else ""
    it = ' font-style="italic"' if italic else ""
    p.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{b}{it}>{esc(s)}</text>')


def chip(x, y, w, s, fill, tcolor):
    rrect(x, y, w, 26, 13, fill)
    txt(x + w / 2, y + 17.5, s, 12, tcolor, bold=True, anchor="middle")


def arrow(x1, y1, x2, y2, color=BLUE, dash=None, sw=3):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mid = "arrG" if color == LINE else ("arrO" if color == AMBER else ("arrGn" if color == GREEN else ("arrR" if color == RED else "arrB")))
    p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#{mid})"/>')


def polyline(pts, color=BLUE, dash=None, sw=3, arrow_end=True):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mid = "arrG" if color == LINE else ("arrO" if color == AMBER else ("arrGn" if color == GREEN else ("arrR" if color == RED else "arrB")))
    m = f' marker-end="url(#{mid})"' if arrow_end else ""
    pstr = " ".join(f"{a},{b}" for a, b in pts)
    p.append(f'<polyline points="{pstr}" fill="none" stroke="{color}" stroke-width="{sw}"{d}{m}/>')


def alabel(x, y, s, color=SUB):
    tw = 8 + len(s) * 6.6
    rrect(x - tw / 2, y - 13, tw, 22, 6, "#ffffff", stroke="#e2e8f0", sw=1)
    txt(x, y + 2, s, 11.5, color, anchor="middle", bold=True)


# ---------- icon glyphs (simplified, Azure palette) ----------
def g_gear(x, y, c=AZ):
    p.append(f'<circle cx="{x}" cy="{y}" r="10" fill="none" stroke="{c}" stroke-width="3"/>')
    for a in range(0, 360, 45):
        import math
        dx, dy = math.cos(math.radians(a)) * 13, math.sin(math.radians(a)) * 13
        p.append(f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="2.6" fill="{c}"/>')
    p.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{c}"/>')


def g_doc(x, y, c=AZ):
    p.append(f'<rect x="{x-9}" y="{y-11}" width="18" height="22" rx="2.5" fill="none" stroke="{c}" stroke-width="3"/>')
    for i in range(3):
        p.append(f'<line x1="{x-5}" y1="{y-4+i*6}" x2="{x+5}" y2="{y-4+i*6}" stroke="{c}" stroke-width="2"/>')


def g_clock(x, y, c=AZ):
    p.append(f'<circle cx="{x}" cy="{y}" r="11" fill="none" stroke="{c}" stroke-width="3"/>')
    p.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y-6}" stroke="{c}" stroke-width="3"/>')
    p.append(f'<line x1="{x}" y1="{y}" x2="{x+5}" y2="{y+2}" stroke="{c}" stroke-width="3"/>')


def g_bolt(x, y, c=AZ):
    p.append(f'<path d="M{x+3},{y-12} L{x-7},{y+2} L{x-1},{y+2} L{x-3},{y+12} L{x+8},{y-3} L{x+1},{y-3} Z" fill="{c}"/>')


def g_nodes(x, y, c=AZ):
    p.append(f'<rect x="{x-4}" y="{y-12}" width="8" height="7" rx="1.5" fill="{c}"/>')
    for dx in (-11, 11):
        p.append(f'<rect x="{x+dx-4}" y="{y+6}" width="8" height="7" rx="1.5" fill="{c}"/>')
        p.append(f'<line x1="{x}" y1="{y-5}" x2="{x+dx}" y2="{y+6}" stroke="{c}" stroke-width="2"/>')


def g_db(x, y, c=AZ):
    p.append(f'<ellipse cx="{x}" cy="{y-8}" rx="11" ry="4" fill="none" stroke="{c}" stroke-width="3"/>')
    p.append(f'<path d="M{x-11},{y-8} V{y+8} a11,4 0 0 0 22,0 V{y-8}" fill="none" stroke="{c}" stroke-width="3"/>')
    p.append(f'<path d="M{x-11},{y} a11,4 0 0 0 22,0" fill="none" stroke="{c}" stroke-width="2"/>')


def g_person(x, y, c=AMBER):
    p.append(f'<circle cx="{x}" cy="{y-7}" r="7" fill="{c}"/>')
    p.append(f'<path d="M{x-12},{y+12} a12,11 0 0 1 24,0 Z" fill="{c}"/>')


def g_shield(x, y, c=AZ):
    p.append(f'<path d="M{x},{y-12} L{x+11},{y-7} V{y+3} a11,13 0 0 1 -11,10 a11,13 0 0 1 -11,-10 V{y-7} Z" fill="{c}"/>')


def g_bar(x, y, c=AZ):
    for i, h in enumerate((8, 16, 12)):
        p.append(f'<rect x="{x-11+i*9}" y="{y+8-h}" width="6" height="{h}" rx="1" fill="{c}"/>')


def g_bulb(x, y, c=VIOLET):
    p.append(f'<circle cx="{x}" cy="{y-3}" r="9" fill="{c}"/>')
    p.append(f'<rect x="{x-4}" y="{y+5}" width="8" height="6" rx="1.5" fill="{c}"/>')


def g_globe(x, y, c=AZ):
    p.append(f'<rect x="{x-11}" y="{y-11}" width="22" height="22" rx="3" fill="none" stroke="{c}" stroke-width="3"/>')
    p.append(f'<circle cx="{x}" cy="{y+1}" r="7" fill="none" stroke="{c}" stroke-width="2"/>')
    p.append(f'<line x1="{x-7}" y1="{y+1}" x2="{x+7}" y2="{y+1}" stroke="{c}" stroke-width="2"/>')
    p.append(f'<line x1="{x-11}" y1="{y-6}" x2="{x+11}" y2="{y-6}" stroke="{c}" stroke-width="2"/>')


def g_check(x, y, c="#ffffff"):
    p.append(f'<path d="M{x-6},{y} L{x-1},{y+5} L{x+7},{y-6}" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')


def g_cross(x, y, c="#ffffff"):
    p.append(f'<line x1="{x-6}" y1="{y-6}" x2="{x+6}" y2="{y+6}" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>')
    p.append(f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>')


def g_loop(x, y, c="#ffffff"):
    p.append(f'<path d="M{x+8},{y-2} a8,8 0 1 1 -3,-6" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<path d="M{x+3},{y-9} L{x+9},{y-9} L{x+8},{y-3} Z" fill="{c}"/>')


def g_azure(x, y):
    p.append(f'<path d="M{x+6},{y-12} L{x+16},{y+10} L{x-4},{y+10} L{x+2},{y-1} L{x+8},{y-1} L{x+5},{y-7} Z" fill="{AZ}"/>')
    p.append(f'<path d="M{x-2},{y-4} L{x-14},{y+10} L{x-4},{y+10} Z" fill="#50b0ef"/>')


# ================= canvas =================
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial">')
p.append('<defs>'
         '<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#94a3b8" flood-opacity="0.25"/></filter>'
         + "".join(
             f'<marker id="{mid}" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto"><path d="M1,1 L10,5.5 L1,10 Z" fill="{col}"/></marker>'
             for mid, col in (("arrB", BLUE), ("arrO", AMBER), ("arrG", LINE), ("arrGn", GREEN), ("arrR", RED)))
         + '</defs>')
p.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# title
txt(W / 2, 52, "Discharge-transition HITL — Durable Task Scheduler", 34, INK, bold=True, anchor="middle")
txt(W / 2, 88, "Human-in-the-loop architecture", 21, BLUE, bold=True, anchor="middle")
chip(W / 2 - 165, 108, 330, "Use case: care-manager approval gate", ZONE, BLUE)

# ---- Azure zone ----
rrect(40, 190, 1380, 760, 18, ZONE, stroke=ZONE_BD, sw=2)
g_azure(80, 228)
txt(105, 236, "Azure", 24, AZ, bold=True)

# Request portal
rrect(70, 340, 250, 165, 12, CARD, stroke="#cfe0f0", sw=2, shadow=True)
g_globe(120, 392, AZ)
txt(80, 452, "Review tracker", 16, INK, bold=True)
txt(80, 476, "Submit case for", 12.5, SUB)
txt(80, 494, "care-manager review", 12.5, SUB)
arrow(320, 420, 468, 420, BLUE)
alabel(394, 405, "Start workflow", BLUE)

# Functions box
rrect(470, 240, 930, 435, 14, CARD, stroke=BLUE, sw=2.5, shadow=True)
g_bolt(505, 278, AMBER)
txt(525, 285, "Azure Functions \u2022 Durable Functions", 19, INK, bold=True)
chip(1200, 262, 180, "Application compute", ZONE, BLUE)

# Orchestrator inner box
rrect(495, 315, 880, 340, 12, INNER, stroke="#bbd6f5", sw=2)
g_nodes(520, 348, AZ)
txt(542, 355, "Orchestrator", 17, INK, bold=True)

# step cards
rrect(515, 385, 200, 110, 10, CARD, stroke="#d7e6f8", sw=1.5, shadow=True)
g_gear(548, 422, AZ)
txt(515 + 100, 470, "Validate packet", 13.5, INK, bold=True, anchor="middle")
arrow(715, 440, 740, 440, BLUE)

rrect(740, 385, 200, 110, 10, CARD, stroke="#d7e6f8", sw=1.5, shadow=True)
g_doc(773, 422, AZ)
txt(740 + 100, 462, "Draft packet +", 13.5, INK, bold=True, anchor="middle")
txt(740 + 100, 481, "notify reviewer", 13.5, INK, bold=True, anchor="middle")
arrow(940, 440, 965, 440, BLUE)

# wait-for-decision big card
rrect(965, 385, 385, 235, 10, CARD, stroke="#d7e6f8", sw=1.5, shadow=True)
g_clock(998, 422, AZ)
txt(1020, 417, "Wait for decision", 15, INK, bold=True)
# sub: external event
rrect(985, 452, 165, 96, 8, INNER, stroke="#cfe0f2", sw=1.2)
g_bolt(1012, 486, AZ)
txt(1035, 482, "External", 12.5, INK, bold=True)
txt(1035, 500, "event", 12.5, INK, bold=True)
txt(1000, 534, "ReviewDecision", 10.5, SUB, mono=True)
# sub: durable timer
rrect(1165, 452, 165, 96, 8, INNER, stroke="#cfe0f2", sw=1.2)
g_clock(1192, 486, AZ)
txt(1215, 482, "Durable timer", 12.5, INK, bold=True)
txt(1215, 500, "SLA \u2022 24 h", 12.5, INK, bold=True)
txt(1180, 534, "create_timer", 10.5, SUB, mono=True)
txt(1157, 585, "Persisted wait \u2022 resumes after restart", 12, MUT, anchor="middle", italic=True)

# DTS box
rrect(330, 715, 1050, 180, 14, DTSBOX, stroke="#b6d3f2", sw=2)
g_nodes(378, 758, AZ)
txt(402, 766, "Durable Task Scheduler (DTS)", 20, INK, bold=True)
chip(1150, 742, 210, "Managed scheduler (Azure service)", "#cfe3fa", BLUE)
for i, (lbl, gi) in enumerate([("Task hub", g_db), ("Durable history & state", g_doc), ("Work-item dispatch", g_gear)]):
    cx = 355 + i * 345
    rrect(cx, 800, 320, 72, 10, CARD, stroke="#cfe0f2", sw=1.5, shadow=True)
    gi(cx + 38, 836, AZ)
    txt(cx + 72, 842, lbl, 14.5, INK, bold=True)

# functions <-> DTS bidirectional
p.append(f'<line x1="830" y1="675" x2="830" y2="715" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrB)" marker-start="url(#arrB)"/>')
alabel(980, 697, "gRPC / TLS \u2022 managed identity", BLUE)

# ---- right column (outside Azure zone) ----
# human approver
rrect(1560, 240, 400, 120, 12, "#fff4e0", stroke=AMBER, sw=2.5, shadow=True)
g_person(1600, 288, AMBER)
txt(1635, 282, "Care manager", 18, INK, bold=True)
txt(1635, 306, "Review \u2022 Approve \u2022 Rework \u2022 Reject", 12.5, AMBTX)
arrow(1400, 300, 1558, 300, BLUE)
alabel(1479, 262, "Notify \u2022 Email / Teams", BLUE)

# approval API
rrect(1560, 400, 400, 120, 12, CARD, stroke=BLUE, sw=2, shadow=True)
g_shield(1600, 452, AZ)
txt(1635, 440, "Approval API", 17, INK, bold=True)
txt(1635, 462, "POST /api/v1/tasks/:id/action", 11.5, SUB, mono=True)
txt(1635, 482, "Entra ID \u2022 validate care-manager role", 12, SUB)
txt(1635, 500, "wrong actor \u2192 403", 11.5, RED, mono=True)
arrow(1760, 360, 1760, 400, AMBER)
alabel(1760, 382, "Submit decision", AMBTX)
# raise external event back into wait card
polyline([(1560, 465), (1470, 465), (1470, 500), (1350, 500)], BLUE)
alabel(1475, 447, "Raise external event \u2022 instance ID", BLUE)

# outcome chips
outs = [
    ("Approved", "Finalize + route plan", GREEN, "#e9f8ee", g_check, "arrGn"),
    ("Needs rework", "Back to draft", AMBER, "#fff4e0", g_loop, "arrO"),
    ("Rejected", "Close case", RED, "#fdecec", g_cross, "arrR"),
    ("Escalated", "SLA 24h \u2022 escalate", AMBER, "#fff4e0", g_clock, "arrO"),
]
oy = 672
cw, gap, x0 = 128, 136, 1440
# manifold: exit wait card bottom, run right above the chips, branch down into each
p.append(f'<line x1="1157" y1="620" x2="1157" y2="650" stroke="{BLUE}" stroke-width="3"/>')
p.append(f'<line x1="1157" y1="650" x2="{x0 + 3 * gap + cw / 2}" y2="650" stroke="{BLUE}" stroke-width="3"/>')
for i, (name, desc, ic, bg, gi, mid) in enumerate(outs):
    ox = x0 + i * gap
    ccx = ox + cw / 2
    col = GREEN if ic == GREEN else (RED if ic == RED else AMBER)
    p.append(f'<line x1="{ccx}" y1="650" x2="{ccx}" y2="{oy}" stroke="{col}" stroke-width="3" marker-end="url(#{mid})"/>')
    rrect(ox, oy, cw, 100, 10, bg, stroke=ic, sw=2, shadow=True)
    p.append(f'<circle cx="{ox+26}" cy="{oy+32}" r="14" fill="{ic}"/>')
    gi(ox + 26, oy + 32, "#ffffff")
    txt(ox + 50, oy + 30, name, 12.5, INK, bold=True)
    txt(ox + 16, oy + 64, desc, 10.5, SUB)

# downstream EHR handoff on approve
rrect(1440, 800, 440, 95, 12, CARD, stroke="#cfe0f0", sw=2, shadow=True)
g_db(1480, 847, AZ)
txt(1515, 838, "Care team handoff / EHR", 15.5, INK, bold=True)
txt(1515, 860, "route approved follow-up plan", 12, SUB)
txt(1515, 878, "synthetic \u2022 human-approved action", 11.5, MUT)
arrow(1504, 772, 1504, 800, GREEN)

# ---- operations / security band ----
rrect(120, 975, 900, 120, 12, "#f8fbff", stroke="#d7e6f8", sw=1.6)
txt(150, 1015, "Operations", 16, INK, bold=True)
p.append(f'<line x1="300" y1="990" x2="300" y2="1080" stroke="#d7e6f8" stroke-width="1.5"/>')
g_bar(345, 1035, AZ)
txt(372, 1041, "DTS dashboard", 14, SUB, bold=True)
p.append(f'<line x1="640" y1="990" x2="640" y2="1080" stroke="#d7e6f8" stroke-width="1.5"/>')
g_bulb(685, 1035, VIOLET)
txt(712, 1041, "Application Insights / LAW", 14, SUB, bold=True)

rrect(1060, 975, 880, 120, 12, "#f8fbff", stroke="#d7e6f8", sw=1.6)
txt(1090, 1015, "Security", 16, INK, bold=True)
p.append(f'<line x1="1230" y1="990" x2="1230" y2="1080" stroke="#d7e6f8" stroke-width="1.5"/>')
g_shield(1280, 1035, AZ)
txt(1312, 1041, "Microsoft Entra ID \u2022 RBAC", 14, SUB, bold=True)

# observability dashed arrows DTS -> ops
polyline([(560, 895), (560, 940), (345, 940), (345, 1018)], LINE, dash="7 6")
polyline([(800, 895), (800, 940), (685, 940), (685, 1018)], LINE, dash="7 6")

# footer tagline + legend
txt(1000, 1128, "Durable orchestration + human judgment + reliable recovery", 16, BLUE, bold=True, anchor="middle")
lx = 1400
p.append(f'<line x1="{lx}" y1="1123" x2="{lx+34}" y2="1123" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrB)"/>')
txt(lx + 42, 1128, "Workflow", 12.5, SUB)
p.append(f'<line x1="{lx+150}" y1="1123" x2="{lx+184}" y2="1123" stroke="{AMBER}" stroke-width="3" marker-end="url(#arrO)"/>')
txt(lx + 192, 1128, "Human decision", 12.5, SUB)
p.append(f'<line x1="{lx+330}" y1="1123" x2="{lx+364}" y2="1123" stroke="{LINE}" stroke-width="3" stroke-dasharray="7 6" marker-end="url(#arrG)"/>')
txt(lx + 372, 1128, "Observability", 12.5, SUB)

txt(44, 1128, "Grounded in agent-service/orchestrations + hitl_dts.py \u2022 synthetic data only", 11, MUT)

p.append("</svg>")

out = os.path.join(os.path.dirname(__file__), "dts-hitl-architecture.svg")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(p))
print("wrote", out)
