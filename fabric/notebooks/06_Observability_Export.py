"""Starter Fabric notebook: export or inspect telemetry.

Use this notebook to correlate Fabric outputs with App Insights/LAW events in later labs.
"""

required_events = [
    "AgentInvocationStarted",
    "RetrievalCompleted",
    "ToolCallCompleted",
    "PolicyDecisionMade",
    "HumanReviewTaskCreated",
    "HumanReviewCompleted",
    "AgentOutputEvaluated",
]

for event in required_events:
    print(event)

