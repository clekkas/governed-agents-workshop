"""Generate the BYOR (Bring Your Own Registry) architecture diagram as SVG.

Reproducible:  python workshop-assets/build_byor_diagram.py
Output:        workshop-assets/byor-jfrog-githubactions-architecture.svg

Azure-style architecture diagram for Bring Your Own Registry for Hosted Agents: GitHub Actions builds
+ tests + gates the agent image and pushes it to JFrog Artifactory (the customer-owned registry) with
keyless OIDC; Microsoft Foundry Hosted Agents / Azure Container Apps pull the governed image using a
managed identity. Grounded in the workshop's keyless-CI posture (OIDC / Workload Identity Federation,
no stored credentials; see docs/retrospective-cloud-activation.md). Proposed/reference design.

Icons are simplified glyphs in brand palettes (not official trademarked product icons).
"""

import math
import os

W, H = 2000, 1040

INK = "#0f172a"; SUB = "#475569"; MUT = "#64748b"
AZ = "#0078d4"; BLUE = "#2563eb"; GH = "#24292f"; FROG = "#41bf47"; FROGD = "#2e8b33"
AMBER = "#f0a500"; AMBTX = "#b45309"; GREEN = "#16a34a"; RED = "#dc2626"; VIOLET = "#7c3aed"
ZONE = "#eaf3fc"; ZONE_BD = "#bcd8f5"; CARD = "#ffffff"; INNER = "#f5f9ff"
GHZONE = "#eef1f4"; GHBD = "#c9d1d9"; FRZONE = "#eefbef"; FRBD = "#bfe8c2"
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
    mid = {BLUE: "arrB", GREEN: "arrGn", FROG: "arrF", VIOLET: "arrV", LINE: "arrG"}.get(color, "arrB")
    p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#{mid})"/>')


def polyline(pts, color=BLUE, dash=None, sw=3):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mid = {BLUE: "arrB", GREEN: "arrGn", FROG: "arrF", VIOLET: "arrV", LINE: "arrG"}.get(color, "arrB")
    pstr = " ".join(f"{a},{b}" for a, b in pts)
    p.append(f'<polyline points="{pstr}" fill="none" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#{mid})"/>')


def alabel(x, y, s, color=SUB):
    tw = 8 + len(s) * 6.6
    rrect(x - tw / 2, y - 13, tw, 22, 6, "#ffffff", stroke="#e2e8f0", sw=1)
    txt(x, y + 2, s, 11.5, color, anchor="middle", bold=True)


# ---------- glyphs ----------
def g_github(x, y, c=GH):
    p.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{c}"/>')
    p.append(f'<path d="M{x},{y-7} a7,7 0 0 0 -2.2,13.6 c0,-0.6 0,-1.4 0,-2 c-3.6,0.8 -4.4,-1.6 -4.4,-1.6 c-0.4,-1 -1,-1.4 -1,-1.4 c-1,-0.7 0,-0.7 0,-0.7 c1,0 1.6,1 1.6,1 c1,1.7 2.7,1.2 3.3,0.9 c0.1,-0.7 0.4,-1.2 0.7,-1.5 c-2.9,-0.3 -5.9,-1.4 -5.9,-6.4 c0,-1.4 0.5,-2.5 1.3,-3.4 c-0.1,-0.3 -0.6,-1.6 0.1,-3.3 c0,0 1,-0.3 3.4,1.3 a12,12 0 0 1 6.2,0 c2.4,-1.6 3.4,-1.3 3.4,-1.3 c0.7,1.7 0.2,3 0.1,3.3 c0.8,0.9 1.3,2 1.3,3.4 c0,5 -3,6.1 -5.9,6.4 c0.5,0.4 0.9,1.2 0.9,2.4 c0,1.7 0,3.1 0,3.6 A7,7 0 0 0 {x},{y-7} Z" fill="#ffffff"/>')


def g_frog(x, y, c=FROG):
    # stylized JFrog-ish rounded mark
    p.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{c}"/>')
    p.append(f'<circle cx="{x-4}" cy="{y-4}" r="3" fill="#ffffff"/>')
    p.append(f'<circle cx="{x+4}" cy="{y-4}" r="3" fill="#ffffff"/>')
    p.append(f'<path d="M{x-6},{y+3} a6,4 0 0 0 12,0" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>')


def g_azure(x, y):
    p.append(f'<path d="M{x+6},{y-12} L{x+16},{y+10} L{x-4},{y+10} L{x+2},{y-1} L{x+8},{y-1} L{x+5},{y-7} Z" fill="{AZ}"/>')
    p.append(f'<path d="M{x-2},{y-4} L{x-14},{y+10} L{x-4},{y+10} Z" fill="#50b0ef"/>')


def g_gear(x, y, c=AZ):
    p.append(f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{c}" stroke-width="3"/>')
    for a in range(0, 360, 45):
        dx, dy = math.cos(math.radians(a)) * 12, math.sin(math.radians(a)) * 12
        p.append(f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="2.3" fill="{c}"/>')
    p.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{c}"/>')


def g_check(x, y, c=GREEN):
    p.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{c}"/>')
    p.append(f'<path d="M{x-5},{y} L{x-1},{y+4} L{x+6},{y-5}" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')


def g_box(x, y, c=AZ):
    p.append(f'<path d="M{x},{y-11} L{x+11},{y-5} V{y+7} L{x},{y+13} L{x-11},{y+7} V{y-5} Z" fill="none" stroke="{c}" stroke-width="2.6"/>')
    p.append(f'<path d="M{x-11},{y-5} L{x},{y+1} L{x+11},{y-5}" fill="none" stroke="{c}" stroke-width="2.2"/>')
    p.append(f'<line x1="{x}" y1="{y+1}" x2="{x}" y2="{y+13}" stroke="{c}" stroke-width="2.2"/>')


def g_shieldcheck(x, y, c=AZ):
    p.append(f'<path d="M{x},{y-12} L{x+11},{y-7} V{y+3} a11,13 0 0 1 -11,10 a11,13 0 0 1 -11,-10 V{y-7} Z" fill="{c}"/>')
    p.append(f'<path d="M{x-5},{y-1} L{x-1},{y+3} L{x+6},{y-5}" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')


def g_key(x, y, c=VIOLET):
    p.append(f'<circle cx="{x-5}" cy="{y}" r="6" fill="none" stroke="{c}" stroke-width="3"/>')
    p.append(f'<line x1="{x}" y1="{y}" x2="{x+11}" y2="{y}" stroke="{c}" stroke-width="3"/>')
    p.append(f'<line x1="{x+11}" y1="{y}" x2="{x+11}" y2="{y+5}" stroke="{c}" stroke-width="3"/>')
    p.append(f'<line x1="{x+7}" y1="{y}" x2="{x+7}" y2="{y+4}" stroke="{c}" stroke-width="3"/>')


def g_scan(x, y, c=FROGD):
    p.append(f'<rect x="{x-11}" y="{y-11}" width="22" height="22" rx="3" fill="none" stroke="{c}" stroke-width="2.6"/>')
    p.append(f'<line x1="{x-11}" y1="{y}" x2="{x+11}" y2="{y}" stroke="{c}" stroke-width="2.6"/>')
    p.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{c}"/>')


def g_tag(x, y, c=FROGD):
    p.append(f'<path d="M{x-11},{y-8} H{x+2} L{x+11},{y} L{x+2},{y+8} H{x-11} Z" fill="none" stroke="{c}" stroke-width="2.6"/>')
    p.append(f'<circle cx="{x-5}" cy="{y}" r="2.4" fill="{c}"/>')


def g_rocket(x, y, c=AZ):
    p.append(f'<path d="M{x},{y-12} c6,3 7,11 4,17 h-8 c-3,-6 -2,-14 4,-17 Z" fill="none" stroke="{c}" stroke-width="2.6"/>')
    p.append(f'<circle cx="{x}" cy="{y-3}" r="2.6" fill="{c}"/>')
    p.append(f'<path d="M{x-4},{y+8} l-3,6 M{x+4},{y+8} l3,6" stroke="{c}" stroke-width="2.4"/>')


# ================= canvas =================
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial">')
p.append('<defs>'
         '<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#94a3b8" flood-opacity="0.25"/></filter>'
         + "".join(f'<marker id="{mid}" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto"><path d="M1,1 L10,5.5 L1,10 Z" fill="{col}"/></marker>'
                   for mid, col in (("arrB", BLUE), ("arrGn", GREEN), ("arrF", FROG), ("arrV", VIOLET), ("arrG", LINE)))
         + '</defs>')
p.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# title
txt(W / 2, 52, "Bring Your Own Registry (BYOR) for Hosted Agents", 33, INK, bold=True, anchor="middle")
txt(W / 2, 88, "Keyless CI/CD with JFrog Artifactory + GitHub Actions", 20, BLUE, bold=True, anchor="middle")
chip(W / 2 - 185, 108, 370, "Use case: governed image provenance & promotion", ZONE, BLUE)

ZY, ZH = 175, 610

# ===== GitHub zone =====
rrect(40, ZY, 560, ZH, 18, GHZONE, stroke=GHBD, sw=2)
g_github(78, ZY + 40, GH)
txt(100, ZY + 47, "GitHub", 22, GH, bold=True)

rrect(70, ZY + 70, 500, 90, 12, CARD, stroke="#cbd5e1", sw=2, shadow=True)
g_box(112, ZY + 115, GH)
txt(148, ZY + 108, "Source repo", 16, INK, bold=True)
txt(148, ZY + 130, "agent code \u2022 Dockerfile \u2022 eval datasets \u2022 IaC", 12, SUB)

# GitHub Actions CI box
rrect(70, ZY + 185, 500, 385, 12, CARD, stroke=GH, sw=2.5, shadow=True)
g_gear(108, ZY + 222, GH)
txt(130, ZY + 229, "GitHub Actions \u2022 CI", 18, INK, bold=True)
stages = [
    ("Build agent image", "docker build (Dockerfile)", g_box),
    ("Test + eval release gate", "golden + adversarial; fail-closed", g_check),
    ("Contract + policy checks", "MCP contracts \u2022 guardrails", g_shieldcheck),
    ("Push image (keyless)", "OIDC token \u2022 no stored creds", g_key),
]
for i, (t, d, gi) in enumerate(stages):
    yy = ZY + 255 + i * 78
    rrect(95, yy, 450, 66, 10, INNER, stroke="#d7dde3", sw=1.4, shadow=True)
    gi(128, yy + 33, GH if gi in (g_box,) else (GREEN if gi == g_check else (AZ if gi == g_shieldcheck else VIOLET)))
    txt(160, yy + 28, t, 14.5, INK, bold=True)
    txt(160, yy + 48, d, 11.5, SUB, mono=True)
    if i < 3:
        p.append(f'<line x1="320" y1="{yy+66}" x2="320" y2="{yy+78}" stroke="{GH}" stroke-width="2.4" marker-end="url(#arrG)"/>')

arrow(300, ZY + 160, 300, ZY + 185, GH := LINE)  # source -> CI (neutral)

# ===== JFrog zone =====
rrect(650, ZY, 620, ZH, 18, FRZONE, stroke=FRBD, sw=2)
g_frog(690, ZY + 40, FROG)
txt(712, ZY + 47, "JFrog Artifactory", 22, FROGD, bold=True)
chip(1080, ZY + 22, 170, "BYO container registry", "#d7f3d9", FROGD)

cards = [
    ("Docker repository", "governed agent images \u2022 virtual + remote repos", g_box, AZ),
    ("Xray security scan", "CVE + license policy gate on push", g_scan, FROGD),
    ("Immutable tags + promotion", "dev \u2192 staging \u2192 prod (signed, provenance)", g_tag, FROGD),
    ("OIDC token exchange", "identity-based \u2022 no long-lived registry keys", g_key, VIOLET),
]
for i, (t, d, gi, c) in enumerate(cards):
    yy = ZY + 90 + i * 118
    rrect(680, yy, 560, 96, 12, CARD, stroke="#cfe0d2", sw=1.8, shadow=True)
    gi(722, yy + 48, c)
    txt(760, yy + 42, t, 16.5, INK, bold=True)
    txt(760, yy + 66, d, 12.5, SUB)

# ===== Azure zone =====
rrect(1320, ZY, 640, ZH, 18, ZONE, stroke=ZONE_BD, sw=2)
g_azure(1360, ZY + 40)
txt(1385, ZY + 47, "Azure \u2022 Microsoft Foundry", 22, AZ, bold=True)

rrect(1350, ZY + 80, 580, 150, 12, CARD, stroke=BLUE, sw=2.5, shadow=True)
g_rocket(1392, ZY + 130, AZ)
txt(1428, ZY + 120, "Hosted Agents", 18, INK, bold=True)
txt(1428, ZY + 144, "Foundry hosted-agent runtime / Azure Container Apps", 12, SUB)
txt(1428, ZY + 164, "pull governed image at deploy \u2022 revision roll", 12, SUB)
txt(1372, ZY + 205, "Discharge Transition Orchestrator + 7 specialists (synthetic)", 12, MUT, italic=True)

rrect(1350, ZY + 255, 580, 120, 12, CARD, stroke="#cfe0f0", sw=2, shadow=True)
g_shieldcheck(1392, ZY + 305, AZ)
txt(1428, ZY + 295, "Trust plane", 16.5, INK, bold=True)
txt(1428, ZY + 318, "user-assigned managed identity + RBAC (AcrPull-equivalent)", 12, SUB)
txt(1428, ZY + 338, "Key Vault \u2022 App Insights / LAW \u2022 private ingress", 12, SUB)

rrect(1350, ZY + 400, 580, 110, 12, "#f8fbff", stroke="#d7e6f8", sw=1.6)
g_check(1392, ZY + 452, GREEN)
txt(1428, ZY + 445, "Why BYOR for KP", 15.5, INK, bold=True)
txt(1428, ZY + 467, "KP keeps image provenance, scanning, and promotion in", 12, SUB)
txt(1428, ZY + 485, "its own registry \u2014 Foundry consumes, does not own, the supply chain.", 12, SUB)

# ===== main flow arrows =====
# CI push -> JFrog docker repo
arrow(570, ZY + 320, 680, ZY + 138, FROG, sw=3.5)
alabel(628, ZY + 210, "push image \u2022 OIDC", FROGD)
# JFrog -> Azure hosted agents (pull)
arrow(1240, ZY + 138, 1350, ZY + 150, GREEN, sw=3.5)
alabel(1296, ZY + 110, "pull image \u2022 managed identity", GREEN)

# ===== identity / keyless band =====
IBY = ZY + ZH + 30
rrect(40, IBY, 1920, 105, 14, "#f6f3fd", stroke="#e0d6f6", sw=1.8)
g_key(90, IBY + 52, VIOLET)
txt(118, IBY + 40, "Identity & keyless trust", 16.5, INK, bold=True)
txt(118, IBY + 62, "No stored registry credentials or client secrets \u2014 every hop uses short-lived, federated identity.", 12.5, SUB)
# federation nodes
fed = [
    ("GitHub OIDC \u2192 Entra WIF", 760),
    ("Azure managed identity \u2192 JFrog OIDC", 1180),
    ("Xray + signing = provenance gate", 1620),
]
for s, cx in fed:
    tw = 20 + len(s) * 7.2
    rrect(cx - tw / 2, IBY + 34, tw, 40, 10, "#ffffff", stroke="#d9cef2", sw=1.4)
    txt(cx, IBY + 59, s, 12.5, VIOLET, bold=True, anchor="middle")

# dashed federation links from zones down to band
polyline([(300, ZY + ZH), (300, IBY)], VIOLET, dash="7 6")
polyline([(960, ZY + ZH), (960, IBY)], VIOLET, dash="7 6")
polyline([(1630, ZY + ZH), (1630, IBY)], VIOLET, dash="7 6")

# footer tagline + legend
txt(760, 1018, "Your registry, your provenance \u2014 governed images, keyless promotion, no stored secrets.", 15.5, BLUE, bold=True, anchor="middle")
lx = 1400
p.append(f'<line x1="{lx}" y1="1013" x2="{lx+34}" y2="1013" stroke="{FROG}" stroke-width="3" marker-end="url(#arrF)"/>')
txt(lx + 42, 1018, "Push / promote", 12.5, SUB)
p.append(f'<line x1="{lx+165}" y1="1013" x2="{lx+199}" y2="1013" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrGn)"/>')
txt(lx + 207, 1018, "Image pull", 12.5, SUB)
p.append(f'<line x1="{lx+310}" y1="1013" x2="{lx+344}" y2="1013" stroke="{VIOLET}" stroke-width="3" stroke-dasharray="7 6" marker-end="url(#arrV)"/>')
txt(lx + 352, 1018, "Federated identity", 12.5, SUB)

txt(44, 1018, "Proposed / reference design \u2022 synthetic data only", 11, MUT)

p.append("</svg>")

out = os.path.join(os.path.dirname(__file__), "byor-jfrog-githubactions-architecture.svg")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(p))
print("wrote", out)
