# Discharge Transition Exception Coordinator

React UI artifact for the Kaiser readmissions agent workshop.

The app showcases the workshop use case: a care manager or ADT nurse reviews synthetic discharge-transition exceptions, sees an approved risk-score response, reviews cited evidence and transition gaps, and records a human review action. It must not provide autonomous clinical actions.

## What this UI demonstrates

1. Synthetic tomorrow-discharge candidate worklist.
2. Case summary and approved risk-score context.
3. Retrieved evidence with citations.
4. Transition gaps, missing information, and guardrail state.
5. Draft exception packet requiring human review.
6. HITL actions: approve for pilot simulation, request rework, reject.
7. Observability cues: correlation ID, policy decisions, tool calls, and trace events.

## Local development

```powershell
npm install
npm run dev
```

## Build

```powershell
npm run build
```

The UI uses static synthetic sample data for the first workshop artifact. Later phases can wire it to the hosted agent and MCP server.
