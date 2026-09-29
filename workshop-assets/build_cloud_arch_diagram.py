"""Generate the Option B cloud-activation architecture diagram (Azure + GitHub + connectors) as SVG."""

W, H = 1680, 1180

TEAL = "#0f766e"; INK = "#0f172a"; SUB = "#475569"; LINE = "#94a3b8"
AZURE = "#0078d4"; GH = "#24292f"; AMBER = "#b45309"; RED = "#dc2626"; GREEN = "#16a34a"; VIOLET = "#7c3aed"

parts = []


def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines=None, fill="#ffffff", border=TEAL, accent=None, dashed=False, tsize=15):
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{border}" stroke-width="2"{dash}/>')
    if accent:
        parts.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>')
    parts.append(f'<text x="{x+16}" y="{y+24}" font-family="Segoe UI, Arial" font-size="{tsize}" font-weight="700" fill="{INK}">{esc(title)}</text>')
    if lines:
        for i, ln in enumerate(lines):
            parts.append(f'<text x="{x+16}" y="{y+46+i*18}" font-family="Segoe UI, Arial" font-size="11.5" fill="{SUB}">{esc(ln)}</text>')


def zone(x, y, w, h, label, color, fill):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{color}" stroke-width="1.6" stroke-dasharray="3 5"/>')
    parts.append(f'<text x="{x+16}" y="{y+22}" font-family="Segoe UI, Arial" font-size="12.5" font-weight="800" fill="{color}" letter-spacing="1">{esc(label)}</text>')


def arrow(x1, y1, x2, y2, label=None, color=LINE, dashed=False, lx=None, ly=None, width=2.2):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#arw)"/>')
    if label:
        mx = lx if lx is not None else (x1+x2)/2
        my = ly if ly is not None else (y1+y2)/2
        tw = 9 + len(label)*6.3
        parts.append(f'<rect x="{mx-tw/2:.0f}" y="{my-12:.0f}" width="{tw:.0f}" height="21" rx="6" fill="#ffffff" stroke="{color}" stroke-width="1"/>')
        parts.append(f'<text x="{mx:.0f}" y="{my+2:.0f}" font-family="Segoe UI, Arial" font-size="11" fill="{SUB}" text-anchor="middle">{esc(label)}</text>')


def num(x, y, n, color=AZURE):
    parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{color}"/>')
    parts.append(f'<text x="{x}" y="{y+4}" font-family="Segoe UI, Arial" font-size="13" font-weight="800" fill="#ffffff" text-anchor="middle">{n}</text>')


parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append('<defs><marker id="arw" markerWidth="12" markerHeight="12" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#64748b"/></marker></defs>')
parts.append(f'<rect width="{W}" height="{H}" fill="#f8fafc"/>')

parts.append(f'<text x="40" y="46" font-family="Segoe UI, Arial" font-size="25" font-weight="800" fill="{TEAL}">Governed Terraform CI/CD on a private-only Azure tenant (Option B)</text>')
parts.append(f'<text x="40" y="72" font-family="Segoe UI, Arial" font-size="13.5" fill="{SUB}">Self-hosted GitHub runner on an Azure VNet reaches remote Terraform state via a private endpoint; keyless auth via Entra Workload Identity Federation (OIDC).</text>')

# ---- GitHub zone (left) ----
zone(40, 100, 470, 470, "GITHUB (github.com — enterprise managed)", GH, "#f3f4f6")
box(64, 140, 420, 92, "Repository  ·  clekkas/governed-agents-inpractice-workshop", [
    "Terraform config (infra/terraform), app + agent-service",
    "Secrets: AZURE_CLIENT_ID / TENANT / SUBSCRIPTION",
    "Variables: TFSTATE_RESOURCE_GROUP / STORAGE_ACCOUNT / CONTAINER / KEY"], fill="#ffffff", border=GH, accent=GH)
box(64, 250, 420, 104, "GitHub Actions workflows", [
    "ci.yml          -> app tests, MCP contracts, eval gate (hosted runner)",
    "terraform-plan  -> fmt/validate/plan on PR (self-hosted)",
    "terraform-apply -> gated apply, environment 'production' (self-hosted)"], fill="#ffffff", border=AZURE, accent=AZURE)
box(64, 372, 420, 70, "OIDC token issuer", [
    "token.actions.githubusercontent.com",
    "sub: repo:clekkas@314357/...@1393826284:ref:refs/heads/main"], fill="#eef2ff", border=VIOLET, accent=VIOLET)
box(64, 460, 420, 92, "Entra Workload Identity Federation", [
    "App reg gh-oidc-foundry-phase2 (client 0882f573...)",
    "Federated credentials match the ID-embedded subject",
    "No client secret — short-lived token exchange"], fill="#eef2ff", border=VIOLET, accent=VIOLET)

# ---- Azure zone (right) ----
zone(560, 100, 1080, 1010, "AZURE SUBSCRIPTION  ·  MCAPS  ·  Policy: private-only storage, no public VM IPs", AZURE, "#eff6ff")

# Entra / identity
box(590, 140, 480, 96, "Microsoft Entra ID", [
    "OIDC app + service principal (04779896...)",
    "Roles: Contributor + User Access Administrator (subscription)",
    "Storage Blob Data Contributor (state account)"], fill="#ffffff", border=VIOLET, accent=VIOLET)

# Resource group
zone(590, 260, 1020, 700, "RESOURCE GROUP  rg-tfstate-foundry-phase2  (eastus2)", TEAL, "#f0fdfa")

# VNet
zone(610, 300, 720, 470, "VNET  vnet-tfrunner  10.20.0.0/16", AZURE, "#e0f2fe")
# runner subnet
zone(628, 340, 340, 400, "snet-runner 10.20.1.0/24", "#0369a1", "#f0f9ff")
box(648, 378, 300, 150, "Self-hosted runner VM", [
    "vm-ghrunner  ·  Standard_D2s_v3",
    "private IP 10.20.1.4  ·  NO public IP",
    "GitHub Actions runner (systemd)",
    "az CLI + git + terraform",
    "labels: self-hosted, azure-vnet",
    "system managed identity"], fill="#ffffff", border=AZURE, accent=AZURE)
box(648, 542, 300, 66, "Outbound to github.com", [
    "long-poll for jobs (no inbound)",
    "configured via az vm run-command"], fill="#f8fafc", border=LINE, accent=LINE, tsize=12)
box(648, 622, 300, 96, "What runs here", [
    "terraform init (remote backend)",
    "fmt / validate / plan / apply",
    "az storage container create",
    "azure/login (OIDC)"], fill="#f0fdfa", border=TEAL, accent=TEAL, tsize=12)

# PE subnet
zone(986, 340, 326, 400, "snet-pe 10.20.2.0/24", "#0369a1", "#f0f9ff")
box(1006, 388, 286, 92, "Private Endpoint", [
    "pe-tfstate-blob",
    "NIC private IP 10.20.2.4",
    "group: blob"], fill="#ffffff", border=GREEN, accent=GREEN)
box(1006, 496, 286, 92, "Private DNS zone", [
    "privatelink.blob.core.windows.net",
    "A: sttfstategovagent01 -> 10.20.2.4",
    "linked to vnet-tfrunner"], fill="#ffffff", border=GREEN, accent=GREEN)

# storage (target of PE) — inside RG, right column
box(1360, 340, 230, 220, "Terraform state", [
    "Storage account",
    "sttfstategovagent01",
    "",
    "container: tfstate",
    "key: foundry-phase2",
    ".tfstate",
    "",
    "public access: DISABLED",
    "shared key: DISABLED",
    "reachable only via PE"], fill="#ffffff", border=RED, accent=RED, tsize=13)

# Target infra (planned, not applied)
box(610, 800, 1000, 140, "Target workload infrastructure  (terraform plan: 22 to add — NOT yet applied)", [
    "Foundry (AI Services) account + project + model deployment   ·   Azure AI Search (Foundry IQ / RAG)",
    "Container Apps environment + app (backend + UI) with agent-service sidecar   ·   Azure Container Registry",
    "Key Vault (RBAC)   ·   Storage + container (RAG docs)   ·   Log Analytics + Application Insights",
    "User-assigned managed identity + least-privilege role assignments (AcrPull, KV Secrets User, ...)"],
    fill="#fffbeb", border=AMBER, accent=AMBER, dashed=True, tsize=14)

# ---- connectors / numbered flow ----
# PE -> storage
arrow(1292, 434, 1360, 420, "private link", color=GREEN, lx=1326, ly=402)
# runner -> PE (private DNS resolves to PE)
arrow(948, 452, 1006, 440, "10.20.2.4", color=GREEN)
# GitHub Actions -> runner (job dispatch)
num(524, 300, 1); arrow(484, 300, 648, 430, "1  dispatch job (outbound long-poll)", color=GH, lx=545, ly=345)
# OIDC issuer -> Entra federation (trust)
num(524, 407, 2); arrow(484, 407, 590, 188, "2  present OIDC token", color=VIOLET, lx=548, ly=250)
# Entra -> runner (token) / SP roles
num(1074, 300, 3); arrow(1070, 188, 830, 378, "3  federated token -> Azure access", color=VIOLET, lx=980, ly=250)
# runner -> state (through PE)
num(958, 470, 4); arrow(948, 470, 986, 470, None, color=GREEN)
arrow(1150, 588, 1360, 470, "4  read/write state (private)", color=GREEN, lx=1250, ly=520, dashed=True)
# runner -> target infra (apply)
num(1090, 800, 5); arrow(900, 718, 1090, 800, "5  plan / apply", color=AMBER, lx=1010, ly=760)

# legend
parts.append(f'<text x="40" y="{H-70}" font-family="Segoe UI, Arial" font-size="12.5" font-weight="800" fill="{INK}">Flow</text>')
legend = [
    "1  GitHub Actions dispatches a job; the self-hosted runner picks it up over its outbound connection (no inbound).",
    "2  The workflow presents an OIDC token to Entra;  3  a matching federated credential exchanges it for a short-lived Azure token (no stored secret).",
    "4  terraform init/plan reads+writes remote state over the private endpoint (the account has no public access);  5  plan (done) / apply (gated) manages the target infra.",
]
for i, ln in enumerate(legend):
    parts.append(f'<text x="40" y="{H-48+i*17}" font-family="Segoe UI, Arial" font-size="11.5" fill="{SUB}">{esc(ln)}</text>')

parts.append("</svg>")

out = r"C:\Coding\kaiser-readmissions-agent-workshop\workshop-assets\cloud-activation-architecture.svg"
open(out, "w", encoding="utf-8").write("\n".join(parts))
print("wrote", out, len("\n".join(parts)), "bytes")
