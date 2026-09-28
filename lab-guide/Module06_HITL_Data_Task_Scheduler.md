# Module 06: HITL Data Task Scheduler

## Objective

Design the review workflow that keeps operational decisions with humans.

## States

`DraftCreated -> PendingReview -> InReview -> Approved | Rejected | NeedsRework | TimedOut`

## Required behavior

1. Every draft follow-up plan creates a review task.
2. Review tasks include evidence and missing-information fields.
3. Approvals and rejections are audited.
4. Timeouts escalate.
5. Rework creates a revised draft that still requires review.

## Output

Task schema, state machine, and audit requirements.

