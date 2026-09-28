# Scenario Decision Brief

## Recommendation

Refocus the workshop use case from a risk-score-centric readmissions assistant to a **Discharge Transition Exception Coordinator**.

The workshop should preserve the discharge/readmission setting, but the agent should not generate, infer, recalculate, or override readmission risk. Instead, it consumes an existing approved risk score as deterministic tool output and focuses on the more agentic workflow:

1. Assemble minimum-necessary discharge-transition context.
2. Ground required transition steps in effective-dated protocol content.
3. Identify incomplete operational transition elements.
4. Draft owner, due time, and task/outreach text.
5. Stop at a care-manager or ADT-nurse approval gate.
6. Emit audit and observability signals.

## Scenario name

**Tomorrow's Discharge: Close the Transition Gaps Before They Become Exceptions**

## Persona and trigger

| Item | Decision |
| --- | --- |
| Primary user | Care manager or ADT nurse |
| Supporting roles | Hospitalist, pharmacist, social worker, scheduling team, primary-care follow-up team, platform operator |
| Trigger | Synthetic patient appears on tomorrow's discharge-candidate list |
| Agent output | Draft transition-exception packet requiring human review |

## What changed from the previous use case

| Previous framing | New framing |
| --- | --- |
| Agent highlights readmission risk tier | Agent consumes approved risk score from `risk_score.get` |
| Agent drafts follow-up plan | Agent drafts transition-exception packet |
| Center of gravity is risk/readmission | Center of gravity is actionable transition gaps |
| Risk score can distract from orchestration | Risk score is deterministic context with provenance |
| Generic care coordination | Kaiser-specific transition workflow pattern |

## Transition gaps to detect

1. Medication reconciliation incomplete.
2. Follow-up appointment missing or outside required window.
3. Pending test lacks named owner or expected-result window.
4. Durable medical equipment or home-health service not confirmed.
5. Transportation, language, or social-support barrier unresolved.
6. Referral, outreach, or discharge task incomplete.
7. Protocol evidence missing, expired, conflicting, or prompt-injected.

## Hard safety boundary

The agent may draft, cite, assign proposed owners, and create review tasks. It must not:

1. Decide discharge readiness.
2. Make clinical determinations.
3. Interpret clinical significance of pending results.
4. Change discharge, medication, or treatment orders.
5. Send patient-facing instructions without approved human content.
6. Execute patient-impacting actions without human approval.

## First extension

The first extension should be **pending-result and follow-up closure**. It fits the same discharge-transition spine and gives the workshop an objective closed-loop ownership workflow.

