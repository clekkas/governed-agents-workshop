# Module 02: MCP Server and Work IQ Tool Boundary

## Objective

Design a governed tool boundary for patient context, protocol lookup, utilization history, HITL task creation, and audit logging.

## Tools

| Tool | Purpose | Required control |
| --- | --- | --- |
| `patient.get` | Retrieve redacted case summary | Patient-context scope |
| `notes.get` | Retrieve relevant note excerpts | PHI minimization |
| `protocol.search` | Retrieve approved protocol evidence | Citation metadata |
| `utilization.history` | Retrieve prior encounter summary | Aggregation by default |
| `task.create` | Create HITL review task | Human approval required |
| `audit.write` | Record material workflow events | Always on |

## Work IQ pattern

Use Work IQ as a permission-aware enterprise context pattern where appropriate. The agent should not bypass user permissions or tool authorization.

## Output

Tool contracts, scopes, and audit requirements.

