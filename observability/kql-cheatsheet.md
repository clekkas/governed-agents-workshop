# KQL Cheatsheet

These queries assume custom events are emitted with consistent `customDimensions` fields. Adjust table names if your Application Insights workspace uses OpenTelemetry-specific tables.

## Policy decisions

```kusto
customEvents
| where name == "PolicyDecisionMade"
| summarize Count=count() by
    Policy=tostring(customDimensions.policyName),
    Decision=tostring(customDimensions.decision),
    Severity=tostring(customDimensions.severity)
| order by Count desc
```

## Tool call denial rate

```kusto
customEvents
| where name == "ToolCallCompleted"
| summarize
    Calls=count(),
    Denied=countif(tostring(customDimensions.decision) == "deny"),
    Redacted=countif(tostring(customDimensions.decision) == "redact")
  by Tool=tostring(customDimensions.toolName)
| extend DenialRate = todouble(Denied) / todouble(Calls)
| order by DenialRate desc
```

## Retrieval with missing citations

```kusto
customEvents
| where name == "AgentOutputEvaluated"
| extend CitationCount = toint(customDimensions.citationCount)
| where CitationCount == 0
| project timestamp, correlationId=tostring(customDimensions.correlationId), caseId=tostring(customDimensions.caseId), agentVersion=tostring(customDimensions.agentVersion)
```

## HITL backlog

```kusto
customEvents
| where name in ("HumanReviewTaskCreated", "HumanReviewCompleted")
| summarize
    Created=countif(name == "HumanReviewTaskCreated"),
    Completed=countif(name == "HumanReviewCompleted")
  by bin(timestamp, 1h)
| extend BacklogDelta = Created - Completed
```

## Latency by component

```kusto
customEvents
| where name in ("RetrievalCompleted", "ToolCallCompleted", "HumanReviewTaskCreated", "AgentOutputEvaluated")
| summarize
    P50=percentile(todouble(customDimensions.latencyMs), 50),
    P95=percentile(todouble(customDimensions.latencyMs), 95),
    P99=percentile(todouble(customDimensions.latencyMs), 99)
  by name
```

## End-to-end trace by correlation ID

```kusto
let targetCorrelationId = "REPLACE_WITH_CORRELATION_ID";
customEvents
| where tostring(customDimensions.correlationId) == targetCorrelationId
| project timestamp, name, customDimensions
| order by timestamp asc
```

