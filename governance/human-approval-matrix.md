# Human Approval Matrix

| Agent action | Risk zone | Human approval required? | Notes |
| --- | --- | --- | --- |
| Summarize synthetic case | Green | No | Must cite source and avoid unnecessary PHI. |
| Retrieve protocol evidence | Green | No | Source allowlist applies. |
| Summarize approved risk-score context | Green | No | Must include provenance and must not recalculate score. |
| Draft transition-exception packet | Yellow | Yes before operational use | Draft only; cannot execute. |
| Create review task | Yellow | No, but task is pending review | Task creation is allowed; approval is not. |
| Approve exception packet or follow-up action | Red | Human-only | Agent must not approve. |
| Change discharge order | Red | Not allowed | Out of scope. |
| Change medication order | Red | Not allowed | Out of scope. |
| Share patient-specific details externally | Red | Not allowed in workshop | Requires separate governed workflow. |
