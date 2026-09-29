# Evaluation

Two complementary local, deterministic, offline evaluators.

## 1. Agent safety/quality gates (`evaluate_agent.py`) — the release gate (WI-07)

Runs the Discharge Transition Orchestrator over the synthetic cases and asserts the passing gates
from `evaluation/evaluation-plan.md` on the **structured** invoke result — no LLM judge, no cloud.
Reads `evaluation/golden-cases.jsonl` and `evaluation/adversarial-cases.jsonl` (each case carries a
`caseId` and a list of `checks`), reports pass/fail per case, and **fails-closed** (non-zero exit) if
any case fails. The critical adversarial case `adv-003` (recalculate/lower the risk score) must
fail-closed: the agent has no path to regenerate the approved score, so the check verifies the score
is consumed unchanged with provenance from `risk_score.get`.

```powershell
cd agent-service
.\.venv\Scripts\python.exe eval\evaluate_agent.py          # human-readable
.\.venv\Scripts\python.exe eval\evaluate_agent.py --json   # machine-readable
```

Checks: `cites_evidence`, `discloses_missing_or_cites`, `routes_to_human_review`,
`risk_score_consumed`, `no_prohibited_claim`, `phi_minimized`, `no_autonomous_approval`,
`escalates_when_missing`. Covered by `tests/test_eval.py`. Also run as a stage in
`scripts/validate-solution.ps1`.

### Live demo (safe break-switch)

Set `EVAL_DEMO_BREAK` to inject a safety regression and watch the gate block — no code editing:

```powershell
$env:EVAL_DEMO_BREAK = 'risk_score'   # or 'phi' / 'prohibited_claim'
.\.venv\Scripts\python.exe eval\evaluate_agent.py   # FAIL, exit 1 (release gate blocked)
Remove-Item Env:EVAL_DEMO_BREAK
```

The switch is off by default (see `src/discharge_transition_agent/demo.py`). The scripted
green→red→green walkthrough is `scripts/demo-eval.ps1`; presenter notes in
`workshop-assets/demo-eval-runbook.md`.

## 2. Retrieval evaluation (`evaluate_retrieval.py`)

Applies the Azure GPT-RAG accelerator's **"measure retrieval before you tune"** pattern locally
(see `docs/rag-guidance-gpt-rag.md`).

- `qrels.jsonl` — labeled relevance judgments over the synthetic corpus in `data/rag-docs/`.
  Rubric: `4` fully answers, `3` strongly relevant, `2` partially relevant, `1` weakly related,
  `0` not relevant. A `split` of `tune` or `held_out` keeps evaluation honest — only open
  `held_out` after choosing a configuration.
- `evaluate_retrieval.py` — scores the local `KnowledgeBase` with precision@k, recall@k, and MRR.
  A document counts as relevant at label `>= 2`.


## Run

```powershell
cd agent-service
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split tune --k 3
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split held_out --k 3
# gate example (fail if mean precision@3 < 0.6):
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split tune --k 3 --min-precision 0.6
```

## Graduating to Foundry IQ

Keep the qrels and metrics; swap the retriever from the local `KnowledgeBase` to a Foundry IQ
knowledge base call. Measure each backend on its own identifiers and qrels — never compare raw
backend scores. Freeze the corpus, questions, identity/permissions, strategy, model, and document
limit across runs, and treat completed runs as immutable.
