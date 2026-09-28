# Troubleshooting

## Common workshop issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Data files are missing | Synthetic data generator has not run. | Run `python .\data\generate_synthetic_healthcare_data.py --output .\data\synthetic`. |
| Fabric notebook cannot find tables | Lakehouse not attached or data not ingested. | Attach the correct Lakehouse and rerun ingestion. |
| RAG citations are missing | Source metadata not mapped. | Ensure source URL or file path fields are retrievable. |
| Tool call is denied | Scope or patient context mismatch. | Inspect policy decision and audit event. |
| HITL task does not advance | Invalid state transition. | Check `hitl\state-machine.md`. |
| Telemetry cannot be correlated | Missing correlation ID. | Confirm all events include `correlationId`. |

