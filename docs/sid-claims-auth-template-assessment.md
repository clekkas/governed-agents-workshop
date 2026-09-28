# SID Claims Auth AI Agent Template Assessment

Reference repo: `C:\Coding\hls-demos\SID-claims-Auth-AI-Agent`

## Recommendation

Use the repository as a **UI and review-workbench pattern reference**, not as a use-case or domain template.

The source use case is prior authorization / claims / utilization management, which is intentionally out of scope for this workshop. The reusable value is the reviewer experience:

1. Single-case review.
2. Batch review mode.
3. Case selection.
4. Payload audit view.
5. Findings / evidence display.
6. Citation navigation.
7. Recommended next steps.
8. Raw JSON response inspection.
9. Static frontend served by backend.

## What to reuse

| Pattern | Reuse decision |
| --- | --- |
| Single-case deep-dive | Reuse. Adapted to discharge-transition exception review. |
| Batch queue | Reuse. Adapted to tomorrow-discharge candidate worklist. |
| Payload audit view | Reuse. Shows synthetic case payload and approved risk-score context. |
| Citation navigation | Reuse concept. Implemented as citation focus panel in React. |
| Recommended next steps | Reuse. Adapted to reviewer actions and escalation guidance. |
| Raw JSON response | Reuse. Shows draft agent response object. |
| SID-bound auth | Do not reuse directly. Replace with future case/actor/correlation envelope. |
| Prior-auth agents | Do not reuse. Replace with discharge-transition specialist agents. |

## Current workshop UI adaptation

The workshop UI remains React + TypeScript because the rest of the repo is moving toward a richer UI artifact, but it now incorporates the useful review-console flow:

1. Mode toggle: single case / batch review.
2. Batch multi-select and mock run.
3. Drill-in from batch result to single-case view.
4. Payload audit view.
5. Raw agent response view.
6. Citation focus panel.
7. Recommended next steps panel.

## Future backend adaptation

When the backend is introduced, copy the source repo's proven idea of serving the frontend as static content from the app root. Adapt the API shape to:

```text
GET  /api/health
GET  /api/v1/cases
GET  /api/v1/cases/:id
POST /api/v1/agent/invoke
```

But change the domain envelope from claims/prior-auth to discharge-transition exception review.

