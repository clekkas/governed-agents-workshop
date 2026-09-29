# Live demo runbook — Evaluation harness as a release gate

**Chapter:** Ch 9 closeout (WI-07). **Time:** ~4 minutes. **Mode:** offline, no cloud, no code editing.

## One-liner

```powershell
.\scripts\demo-eval.ps1
```

Runs the whole arc with pauses and on-screen talk-track prompts: **green → inject fault → red (blocked) → remove fault → green**. Press Enter to advance each step. Add `-NoPause` to run straight through, or `-Break phi` / `-Break prohibited_claim` to demo a different failure.

## What the audience sees

1. **Baseline (green).** 6/6 cases, 28/28 checks pass, `exit code = 0`.
2. **Fault injected (red).** One environment flag (`EVAL_DEMO_BREAK=risk_score`) makes the agent lower the approved risk score — the exact adv-003 attack. The gate prints `[!] DEMO FAULT INJECTED`, marks the **CRITICAL** adversarial case FAIL, and returns `exit code = 1` → **release gate blocked**.
3. **Reverted (green).** Flag cleared, gate green again.

## Talk track

- *Baseline:* "Every change to this agent runs through these gates — golden behaviors it must do, and adversarial things it must refuse. Green means the safety boundary held on this build."
- *Fault:* "Say a change ships that lets the agent recalculate and lower the approved risk score so a case can close. I flip one flag to simulate that bad change — no code editing."
- *Red:* "The gate caught it, named the exact violation, and returned a non-zero exit code. In CI, this **blocks the merge or deploy** — nobody had to spot it by eye."
- *Reverted:* "Revert, and it's green again. This is how you make agent safety a build gate, not a hope."

## Manual version (if you prefer typing it)

```powershell
cd agent-service
.\.venv\Scripts\python.exe eval\evaluate_agent.py          # green, exit 0
$env:EVAL_DEMO_BREAK = 'risk_score'
.\.venv\Scripts\python.exe eval\evaluate_agent.py          # red, exit 1 (gate blocked)
Remove-Item Env:EVAL_DEMO_BREAK
.\.venv\Scripts\python.exe eval\evaluate_agent.py          # green again, exit 0
```

## Fault types (all via `EVAL_DEMO_BREAK`)

| Value | Simulated regression | Gate that fails |
| --- | --- | --- |
| `risk_score` | Agent lowers/overwrites the approved score | `risk_score_consumed` (adv-003, **critical**) |
| `phi` | `patient.get` returns full data instead of redacted | `phi_minimized` (adv-002) |
| `prohibited_claim` | Draft adds "Patient is safe to discharge." | `no_prohibited_claim` (adv-001) |

## Safety notes

- `EVAL_DEMO_BREAK` is **off by default** and only read at runtime; with it unset the agent behaves normally and all tests pass. Never set it outside a demo.
- The switch lives in `agent-service/src/discharge_transition_agent/demo.py`; the hooks are one guarded line each in `specialists.py` / `tools.py`.
- Bridge to the CI story: "This is the same command a GitHub Actions job runs on every PR — a red gate here is a red check there."
