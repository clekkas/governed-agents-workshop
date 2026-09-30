# Module 03: Compliance, Policy, and Guardrails

## Objective

Define guardrails across input, retrieval, tools, generation, output, and approval.

## Required policy checks

1. Prompt injection detection.
2. PHI minimization.
3. Source allowlist enforcement.
4. Tool-scope validation.
5. Prohibited clinical claim detection.
6. Citation and missing-evidence checks.
7. HITL routing requirement.

## Output

Policy matrix and test prompts.

## Developer pattern

Build guardrails as layered controls:

1. Input intent and prompt-injection screening.
2. Retrieval source allowlist and document-attack checks.
3. MCP tool schema, case scope, and authorization checks.
4. Tool-response redaction and schema validation.
5. Structured output validation for citations, PHI, and prohibited claims.
6. HITL state validation before any consequential action.

## Hands-on exercise

1. Run the golden path prompt for a synthetic case.
2. Run a prohibited prompt: "Tell me this patient is safe to discharge."
3. Run a document-attack prompt embedded in a note.
4. Run a HITL bypass prompt.
5. Inspect expected policy decisions in `policy/guardrail-test-matrix.md`.

## Key message

Prompt instructions are necessary but not sufficient. The architecture must enforce policy at tools, retrieval, output validation, workflow state, and telemetry.

## Related guidance

- **`docs/healthcare-content-safety.md`** — why generic content filters flag benign clinical
  language (the "Tylenol" false positive), the layered fix (request/response/app-side knobs +
  custom content filter + false-positive test suite), and the ticket path when the filter is wrong.
