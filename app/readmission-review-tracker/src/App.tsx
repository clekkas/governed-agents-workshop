import { useEffect, useMemo, useState } from "react";
import { reviewCases } from "./sampleData";
import { fetchCases, invokeAgent, toReviewCase } from "./api";
import type { ReviewCase, ReviewStatus } from "./types";

const statusLabels: Record<ReviewStatus, string> = {
  PendingReview: "Pending review",
  InReview: "In review",
  Approved: "Approved",
  NeedsRework: "Needs rework",
  Rejected: "Rejected",
};

const riskDescriptions: Record<ReviewCase["riskTier"], string> = {
  Critical: "Approved score: immediate exception review",
  High: "Approved score: prioritize transition gaps",
  Medium: "Approved score: review open gaps",
  Low: "Approved score: standard transition workflow",
};

type DataSource = "loading" | "live" | "sample";

function App() {
  const [cases, setCases] = useState(reviewCases);
  const [selectedCaseId, setSelectedCaseId] = useState(reviewCases[0].id);
  const [mode, setMode] = useState<"single" | "batch">("single");
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | undefined>(
    reviewCases[0].evidence[0]?.id,
  );
  const [batchSelection, setBatchSelection] = useState(() => new Set(reviewCases.map((item) => item.id)));
  const [batchResults, setBatchResults] = useState<Record<string, "queued" | "complete">>({});
  const [dataSource, setDataSource] = useState<DataSource>("loading");

  // Load cases from the backend on mount, invoking the orchestrator for each so
  // the worklist and detail panels reflect live agent output. Falls back to the
  // bundled sample data if the backend is unreachable (offline workshop).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const summaries = await fetchCases();
        const results = await Promise.all(
          summaries.map(async (summary) => toReviewCase(summary, await invokeAgent(summary.id))),
        );
        if (cancelled || results.length === 0) return;
        setCases(results);
        setSelectedCaseId(results[0].id);
        setSelectedEvidenceId(results[0].evidence[0]?.id);
        setBatchSelection(new Set(results.map((item) => item.id)));
        setDataSource("live");
      } catch {
        if (!cancelled) setDataSource("sample");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === selectedCaseId) ?? cases[0],
    [cases, selectedCaseId],
  );

  const selectedEvidence =
    selectedCase.evidence.find((item) => item.id === selectedEvidenceId) ?? selectedCase.evidence[0];

  const payloadAudit = useMemo(() => buildPayloadAudit(selectedCase), [selectedCase]);
  const rawResponse = useMemo(() => buildRawResponse(selectedCase), [selectedCase]);

  function updateStatus(status: ReviewStatus) {
    setCases((currentCases) =>
      currentCases.map((item) =>
        item.id === selectedCase.id
          ? {
              ...item,
              status,
              timeline: [
                ...item.timeline,
                {
                  id: `${item.id}-${status}-${Date.now()}`,
                  label: statusLabels[status],
                  actor: "Care manager",
                  timestamp: "Now",
                },
              ],
            }
          : item,
      ),
    );
  }

  function openCase(caseId: string) {
    const nextCase = cases.find((item) => item.id === caseId);
    setSelectedCaseId(caseId);
    setSelectedEvidenceId(nextCase?.evidence[0]?.id);
    setMode("single");
  }

  function toggleBatchCase(caseId: string) {
    setBatchSelection((current) => {
      const next = new Set(current);
      if (next.has(caseId)) {
        next.delete(caseId);
      } else {
        next.add(caseId);
      }
      return next;
    });
  }

  function runBatch() {
    const nextResults: Record<string, "queued" | "complete"> = {};
    for (const caseId of batchSelection) {
      nextResults[caseId] = "complete";
    }
    setBatchResults(nextResults);
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Kaiser Permanente workshop artifact</p>
          <h1>Discharge Transition Exception Coordinator</h1>
          <p className="hero-copy">
            A synthetic ADT nurse and care-manager UI for reviewing transition gaps,
            approved risk-score context, grounded evidence, policy decisions, and HITL state.
          </p>
          <span className={`data-source ${dataSource}`}>
            {dataSource === "loading"
              ? "Connecting to backend…"
              : dataSource === "live"
                ? "Live: backend orchestrator"
                : "Offline: bundled sample data"}
          </span>
        </div>
        <div className="hero-card">
          <span>Trust boundary</span>
          <strong>Exception packets require human approval</strong>
          <p>No autonomous discharge decisions, clinical determinations, or risk-score generation.</p>
        </div>
      </header>

      <div className="mode-tabs" role="tablist" aria-label="Review mode">
        <button
          className={mode === "single" ? "active" : ""}
          onClick={() => setMode("single")}
          role="tab"
          type="button"
        >
          Single case
        </button>
        <button
          className={mode === "batch" ? "active" : ""}
          onClick={() => setMode("batch")}
          role="tab"
          type="button"
        >
          Batch review
        </button>
      </div>

      {mode === "batch" ? (
        <section className="batch-grid">
          <aside className="case-list" aria-label="Batch discharge transition cases">
            <div className="panel-heading">
              <span>Reviewer queue</span>
              <strong>{batchSelection.size} selected</strong>
            </div>
            <div className="batch-actions">
              <button type="button" onClick={() => setBatchSelection(new Set(cases.map((item) => item.id)))}>
                Select all
              </button>
              <button type="button" onClick={() => setBatchSelection(new Set())}>
                Clear
              </button>
              <button type="button" onClick={runBatch} disabled={batchSelection.size === 0}>
                Run selected
              </button>
            </div>
            {cases.map((item) => (
              <label className="batch-case-card" key={item.id}>
                <input
                  checked={batchSelection.has(item.id)}
                  onChange={() => toggleBatchCase(item.id)}
                  type="checkbox"
                />
                <span>
                  <strong>{item.patientLabel}</strong>
                  <small>{item.facility} · {item.diagnosis} · {item.riskTier}</small>
                </span>
              </label>
            ))}
          </aside>

          <section className="case-detail">
            <div className="panel-heading">
              <span>Batch results</span>
              <strong>{Object.keys(batchResults).length} complete</strong>
            </div>
            <div className="batch-results">
              {cases.map((item) => {
                const status = batchResults[item.id] ?? (batchSelection.has(item.id) ? "queued" : undefined);
                return (
                  <article className="batch-result-row" key={item.id}>
                    <div>
                      <strong>{item.patientLabel}</strong>
                      <p>{item.transitionGaps.length} transition gaps · {item.evidence.length} citations · {item.status}</p>
                    </div>
                    <span className={status === "complete" ? "complete" : "queued"}>
                      {status ?? "not selected"}
                    </span>
                    <button type="button" onClick={() => openCase(item.id)}>
                      Drill in
                    </button>
                  </article>
                );
              })}
            </div>
          </section>
        </section>
      ) : (
      <section className="workspace-grid">
        <aside className="case-list" aria-label="Synthetic discharge transition cases">
          <div className="panel-heading">
            <span>Worklist</span>
            <strong>{cases.length} cases</strong>
          </div>
          {cases.map((item) => (
            <button
              className={`case-card ${item.id === selectedCase.id ? "selected" : ""}`}
              key={item.id}
              onClick={() => openCase(item.id)}
              type="button"
            >
              <span className={`risk-dot ${item.riskTier.toLowerCase()}`} />
              <span>
                <strong>{item.patientLabel}</strong>
                <small>{item.facility} · {item.diagnosis}</small>
              </span>
              <em>{statusLabels[item.status]}</em>
            </button>
          ))}
        </aside>

        <section className="case-detail">
          <div className="case-header">
            <div>
              <p className="eyebrow">Synthetic case</p>
              <h2>{selectedCase.patientLabel}</h2>
              <p>{selectedCase.summary}</p>
            </div>
            <div className={`risk-badge ${selectedCase.riskTier.toLowerCase()}`}>
              <span>{selectedCase.riskTier}</span>
              <strong>{Math.round(selectedCase.riskScore * 100)}%</strong>
              <small>{riskDescriptions[selectedCase.riskTier]}</small>
              <small className="risk-source">{selectedCase.riskScoreProvenance}</small>
            </div>
          </div>

          <div className="detail-grid">
            <Panel title="Approved risk context">
              <ul className="clean-list">
                {selectedCase.riskDrivers.map((driver) => (
                  <li key={driver}>{driver}</li>
                ))}
              </ul>
            </Panel>

            <Panel title="Transition exceptions">
              <ul className="clean-list exception">
                {selectedCase.transitionGaps.map((gap) => (
                  <li key={gap}>{gap}</li>
                ))}
              </ul>
            </Panel>

            <Panel title="Missing information">
              <ul className="clean-list warning">
                {selectedCase.missingInformation.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Panel>

            <Panel title="Retrieved evidence">
              <div className="evidence-list">
                {selectedCase.evidence.map((item) => (
                  <button
                    className={`evidence-card ${item.id === selectedEvidence?.id ? "selected" : ""}`}
                    key={item.id}
                    onClick={() => setSelectedEvidenceId(item.id)}
                    type="button"
                  >
                    <div>
                      <strong>{item.source}</strong>
                      <span>{item.confidence} confidence</span>
                    </div>
                    <p>{item.claim}</p>
                    <code>{item.citation}</code>
                  </button>
                ))}
              </div>
            </Panel>

            <Panel title="Citation focus">
              {selectedEvidence ? (
                <article className="citation-focus">
                  <strong>{selectedEvidence.source}</strong>
                  <p>{selectedEvidence.claim}</p>
                  <code>{selectedEvidence.citation}</code>
                </article>
              ) : (
                <p className="muted">Select a citation to inspect the supporting evidence.</p>
              )}
            </Panel>

            <Panel title="Draft exception packet">
              <ol className="plan-list">
                {selectedCase.draftPlan.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <div className="review-actions">
                <button type="button" onClick={() => updateStatus("Approved")}>
                  Approve packet
                </button>
                <button type="button" onClick={() => updateStatus("NeedsRework")}>
                  Request rework
                </button>
                <button type="button" onClick={() => updateStatus("Rejected")}>
                  Reject
                </button>
              </div>
            </Panel>

            <Panel title="Recommended next steps">
              <ul className="clean-list">
                <li>Review each proposed owner and due time before approval.</li>
                <li>Request rework if citation mapping is missing or incomplete.</li>
                <li>Escalate if clinical significance, discharge readiness, or patient instructions are required.</li>
              </ul>
            </Panel>

            <Panel title="Payload audit view">
              <pre className="json-panel">{JSON.stringify(payloadAudit, null, 2)}</pre>
            </Panel>

            <Panel title="Raw agent response">
              <pre className="json-panel">{JSON.stringify(rawResponse, null, 2)}</pre>
            </Panel>
          </div>
        </section>

        <aside className="ops-panel" aria-label="Agent operations">
          <Panel title="Review state">
            <div className={`status-pill ${selectedCase.status.toLowerCase()}`}>
              {statusLabels[selectedCase.status]}
            </div>
            <p className="muted">Due: {selectedCase.due}</p>
          </Panel>

          <Panel title="Tool and policy calls">
            <div className="tool-list">
              {selectedCase.toolCalls.map((call) => (
                <div className="tool-row" key={call.id}>
                  <span>{call.name}</span>
                  <strong className={call.decision}>{call.decision}</strong>
                  <small>{call.latencyMs} ms</small>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Multi-agent orchestration">
            <div className="agent-list">
              {selectedCase.agentContributions.map((agent) => (
                <article className="agent-card" key={agent.id}>
                  <div>
                    <strong>{agent.agentName}</strong>
                    <span className={agent.status}>{agent.status}</span>
                  </div>
                  <small>{agent.role}</small>
                  <p>{agent.summary}</p>
                  {agent.handoffTo ? <em>Handoff: {agent.handoffTo}</em> : null}
                </article>
              ))}
            </div>
          </Panel>

          <Panel title="Trace timeline">
          <div className="trace-id">{selectedCase.correlationId}</div>
            <div className="timeline">
              {selectedCase.timeline.map((event) => (
                <div className="timeline-row" key={event.id}>
                  <span>{event.timestamp}</span>
                  <div>
                    <strong>{event.label}</strong>
                    <small>{event.actor}</small>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </aside>
      </section>
      )}
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="panel">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default App;

function buildPayloadAudit(reviewCase: ReviewCase) {
  return {
    case_id: reviewCase.id,
    patient_label: reviewCase.patientLabel,
    facility: reviewCase.facility,
    diagnosis: reviewCase.diagnosis,
    approved_risk_score: {
      tier: reviewCase.riskTier,
      score: reviewCase.riskScore,
      provenance: reviewCase.riskScoreProvenance,
    },
    transition_gaps: reviewCase.transitionGaps,
    missing_information: reviewCase.missingInformation,
    evidence_sources: reviewCase.evidence.map((item) => ({
      source: item.source,
      citation: item.citation,
      claim: item.claim,
    })),
  };
}

function buildRawResponse(reviewCase: ReviewCase) {
  return {
    summary: reviewCase.summary,
    transition_exceptions: reviewCase.transitionGaps,
    draft_exception_packet: reviewCase.draftPlan,
    citations: reviewCase.evidence,
    tool_calls: reviewCase.toolCalls,
    agent_handoffs: reviewCase.agentContributions,
    review_state: reviewCase.status,
    correlation_id: reviewCase.correlationId,
  };
}
