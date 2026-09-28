"""Starter Fabric notebook: evaluation outline for data and agent answers."""

evaluation_dimensions = [
    "groundedness",
    "safety",
    "phi_minimization",
    "tool_authorization",
    "hitl_routing",
]

for dimension in evaluation_dimensions:
    print(f"Evaluate: {dimension}")

