# Functional Requirements — Discharge Transition Exception Coordinator

Status: Draft for workshop build. Owner: Scout (workshop orchestrator). Implementer: GitHub Copilot.

## Actors

| Actor | Description |
| --- | --- |
| Care manager / ADT nurse | Primary reviewer of discharge-transition exceptions. |
| Discharge Transition Orchestrator | Coordinates specialist agents. |
| Specialist agents | Case context, risk score, evidence retrieval, transition exception, care plan drafting, policy guardrail, human review. |
| Platform operator | Monitors telemetry, evaluations, and incidents. |

## Functional requirements

### FR-1 Case worklist
- The UI shows a worklist of synthetic tomorrow-discharge candidates.
- Each item shows patient label, facility, diagnosis, and approved risk tier.
- Data comes from `GET /api/v1/cases`.

### FR-2 Case review (single)
- Selecting a case invokes the workflow (`POST /api/v1/agent/invoke`).
- The detail view shows: approved risk-score context with provenance, transition exceptions,
  missing information, retrieved evidence with citations, a citation focus panel, a draft
  exception packet, recommended next steps, payload audit view, and raw agent response.

### FR-3 Approved risk score
- The risk score is retrieved via `risk_score.get` and displayed with tier, score, and provenance.
- The system never generates, recalculates, or overrides it.

### FR-4 Grounded evidence (RAG)
- Evidence comes from approved sources only, with citation metadata.
- Missing or conflicting evidence is disclosed and routed to human review, never guessed.

### FR-5 Transition gap detection
- The workflow identifies incomplete transition elements (medication reconciliation,
  follow-up appointment, pending-result ownership, DME/home-health, transportation,
  language, social support, referral, task completion).

### FR-6 Draft exception packet
- The system drafts proposed owners and due times per gap.
- The packet is a draft only and always requires human review.

### FR-7 Human-in-the-loop
- The reviewer can approve, request rework, or reject in the UI.
- Approval/rework/reject actions update review state and timeline.
- No consequential action executes without human approval.

### FR-8 Batch review
- The reviewer can multi-select cases and run them as a batch.
- Results show per-case status; the reviewer can drill into a single case.

### FR-9 Observability cues
- The UI surfaces correlation ID, tool/policy calls, and agent handoffs.
- Every workflow run is traceable end to end via `x-correlation-id`.

### FR-10 Safety enforcement
- Prohibited outputs (safe-to-discharge, clinical determination, order changes,
  generated risk score) are blocked at the tool/policy layer, not only in prompts.

## Out of scope (workshop)

1. Real EHR/Epic integration (mock only).
2. Real PHI.
3. Real Entra SSO and production auth.
4. Write-back to any clinical system.
5. Mobile-first layout.

## Acceptance signals

- `GET /api/health` returns 200.
- `GET /api/v1/cases` returns the synthetic worklist.
- `POST /api/v1/agent/invoke` returns a valid exception packet with correlation ID.
- Case P0310 returns `policyDecision: escalate` (missing specialty protocol).
- Frontend build and `scripts/validate.ps1` pass.
