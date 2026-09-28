# PHI Minimization

## Default behavior

1. Return redacted summaries where possible.
2. Use patient-case identifiers rather than unnecessary demographics.
3. Do not expose free-text notes unless the caller has a logged scope.
4. Preserve the purpose of access in audit logs.

## Escalated behavior

Escalated access requires explicit scope, purpose, patient context, and audit event.

