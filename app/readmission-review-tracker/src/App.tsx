import { useEffect, useMemo, useRef, useState } from "react";
import { reviewCases } from "./sampleData";
import { applyTaskAction, ApiError, fetchCases, fetchLogs, fetchTask, fetchTrace, invokeAgent, toReviewCase } from "./api";
import type { LogEntry, Trace, TraceEvent } from "./api";
import type { ReviewCase, ReviewStatus } from "./types";

const statusLabels: Record<ReviewStatus, string> = {
  PendingReview: "Pending review",
  InReview: "In review",
  Approved: "Approved",
  NeedsRework: "Needs rework",
  Rejected: "Rejected",
  Escalated: "Escalated",
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
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsOffline, setLogsOffline] = useState(false);
  const logSeqRef = useRef(0);
  const [actionMessage, setActionMessage] = useState<{ text: string; kind: "success" | "error" | "info" } | null>(null);
  const [reviewerName, setReviewerName] = useState("");
  const [trace, setTrace] = useState<Trace | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);

  // Load cases from the backend on mount, invoking the orchestrator for each so
  // the worklist and detail panels reflect live agent output. Uses allSettled so a single
  // slow/failed invoke (e.g. a cold start) doesn't discard the whole live worklist — we keep
  // every case that succeeded and only fall back to the bundled sample data if the backend is
  // unreachable or every invoke failed (offline workshop).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const summaries = await fetchCases();
        const settled = await Promise.allSettled(
          summaries.map(async (summary) => toReviewCase(summary, await invokeAgent(summary.id))),
        );
        if (cancelled) return;
        const results = settled
          .filter((s): s is PromiseFulfilledResult<ReviewCase> => s.status === "fulfilled")
          .map((s) => s.value);
        if (results.length === 0) {
          setDataSource("sample");
          return;
        }
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

  // Poll the backend activity log so the UI shows a live feed of what the server is doing —
  // a lightweight preview of the observability chapter. Silently no-ops when offline.
  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const { logs: fresh, lastSeq } = await fetchLogs(logSeqRef.current, 100);
        if (cancelled) return;
        setLogsOffline(false);
        if (fresh.length) {
          logSeqRef.current = lastSeq;
          setLogs((prev) => [...prev, ...fresh].slice(-100));
        }
      } catch {
        if (!cancelled) setLogsOffline(true);
      }
    }
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === selectedCaseId) ?? cases[0],
    [cases, selectedCaseId],
  );

  const selectedEvidence =
    selectedCase.evidence.find((item) => item.id === selectedEvidenceId) ?? selectedCase.evidence[0];

  // Approve / request-changes / reject are only legal from PendingReview or InReview (matches the
  // backend state machine) AND only against live backend data. Sample/placeholder cards (shown
  // while loading or when the backend is unreachable) carry synthetic correlation ids the backend
  // has no durable task for, so acting on them would 404 — disable actions until data is live.
  const isLive = dataSource === "live";
  const statusActionable = ["PendingReview", "InReview"].includes(selectedCase.status);
  const isActionable = isLive && statusActionable;
  // A reviewer must identify themselves before any decision — the name becomes the audited actor.
  const reviewer = reviewerName.trim();
  const canAct = isActionable && reviewer.length > 0;

  const payloadAudit = useMemo(() => buildPayloadAudit(selectedCase), [selectedCase]);
  const rawResponse = useMemo(() => buildRawResponse(selectedCase), [selectedCase]);

  // Reset per-case review inputs when the selected case changes.
  useEffect(() => {
    setActionMessage(null);
    setReviewerName("");
  }, [selectedCaseId]);

  function updateStatus(status: ReviewStatus, note?: string, actor = "Care manager") {
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
                  label: note ? `${statusLabels[status]} · ${note}` : statusLabels[status],
                  actor,
                  timestamp: "Now",
                },
              ],
            }
          : item,
      ),
    );
  }

  // Send the decision to the durable review task (Data Task Scheduler gate). The backend is the
  // source of truth: on success we reflect the returned state; on a server rejection (4xx) we
  // re-sync to the real task state and show the reason — we never optimistically flip the UI to the
  // attempted status. Only a genuine network failure falls back to a local (offline) update.
  const actionVerb: Record<"approve" | "request_changes" | "reject", string> = {
    approve: "Approved packet",
    request_changes: "Requested rework",
    reject: "Rejected packet",
  };

  async function applyReviewAction(action: "approve" | "request_changes" | "reject") {
    if (!isActionable || !reviewer) return;
    try {
      const task = await applyTaskAction(selectedCase.correlationId, action, reviewer);
      updateStatus(task.status as ReviewStatus, actionVerb[action], reviewer);
      setActionMessage({ text: `${actionVerb[action]} by ${reviewer} — task is now ${task.status}.`, kind: "success" });
    } catch (err) {
      if (err instanceof ApiError) {
        // The state machine refused this transition. Re-sync the UI to the true server state.
        try {
          const current = await fetchTask(selectedCase.correlationId);
          updateStatus(current.status as ReviewStatus);
          setActionMessage({
            text: `Action not allowed — the task is ${current.status}. ${err.detail}`,
            kind: "error",
          });
        } catch {
          setActionMessage({ text: `Action not allowed. ${err.detail}`, kind: "error" });
        }
      } else {
        // Network/unreachable (offline workshop against sample data) — local optimistic update.
        const fallback: Record<typeof action, ReviewStatus> = {
          approve: "Approved",
          request_changes: "NeedsRework",
          reject: "Rejected",
        };
        updateStatus(fallback[action], "offline");
        setActionMessage({ text: `Backend offline — reflected ${fallback[action]} locally only.`, kind: "info" });
      }
    }
  }

  // Open the full correlation trace for a run (from a clickable log-line correlation ID).
  async function openTrace(correlationId: string) {
    setTraceError(null);
    try {
      const result = await fetchTrace(correlationId);
      setTrace(result);
    } catch (err) {
      setTrace(null);
      setTraceError(
        err instanceof ApiError && err.status === 404
          ? `No trace found for ${correlationId}.`
          : `Could not load trace for ${correlationId}.`,
      );
    }
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
              <div className="reviewer-field">
                <label htmlFor="reviewer-name">Reviewer name</label>
                <input
                  id="reviewer-name"
                  type="text"
                  value={reviewerName}
                  onChange={(event) => setReviewerName(event.target.value)}
                  placeholder="Enter your name to enable review actions"
                  autoComplete="off"
                  disabled={!isActionable}
                />
              </div>
              <div className="review-actions">
                <button type="button" onClick={() => applyReviewAction("approve")} disabled={!canAct}>
                  Approve packet
                </button>
                <button type="button" onClick={() => applyReviewAction("request_changes")} disabled={!canAct}>
                  Request rework
                </button>
                <button type="button" onClick={() => applyReviewAction("reject")} disabled={!canAct}>
                  Reject
                </button>
              </div>
              {!isLive ? (
                <p className="action-hint">
                  {dataSource === "loading"
                    ? "Loading live cases from the backend — review actions enable once the data arrives."
                    : "Showing bundled sample data (backend unavailable) — review actions are disabled."}
                </p>
              ) : !statusActionable ? (
                <p className="action-hint">
                  This packet is <strong>{statusLabels[selectedCase.status]}</strong> — no further care-manager
                  action is available.
                </p>
              ) : !reviewer ? (
                <p className="action-hint">Enter your reviewer name above — every decision is recorded against it.</p>
              ) : null}
              {actionMessage ? (
                <p className={`action-message ${actionMessage.kind}`}>{actionMessage.text}</p>
              ) : null}
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

      <section className="log-console" aria-label="Backend activity log">
        <div className="log-console-head">
          <h3>Backend activity log</h3>
          <span className={logsOffline ? "log-status offline" : "log-status live"}>
            {logsOffline ? "backend offline" : "live · polling /api/v1/logs"}
          </span>
        </div>
        <div className="log-stream">
          {logs.length === 0 ? (
            <p className="log-empty">Waiting for backend activity…</p>
          ) : (
            [...logs].reverse().map((entry) => (
              <div className={`log-line ${entry.level}`} key={entry.seq}>
                <span className="log-time">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                <span className={`log-level ${entry.level}`}>{entry.level}</span>
                <span className="log-msg">{entry.message}</span>
                {entry.correlationId ? (
                  <button
                    type="button"
                    className="log-trace-link"
                    title={`Open trace ${entry.correlationId}`}
                    onClick={() => openTrace(entry.correlationId as string)}
                  >
                    trace ↗
                  </button>
                ) : (
                  <span />
                )}
              </div>
            ))
          )}
        </div>
        {traceError ? <p className="trace-error">{traceError}</p> : null}
      </section>

      {trace ? (
        <div className="trace-overlay" role="dialog" aria-label="Correlation trace" onClick={() => setTrace(null)}>
          <div className="trace-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="trace-drawer-head">
              <div>
                <h3>Correlation trace</h3>
                <p className="trace-meta">
                  {trace.caseId ? `${trace.caseId} · ` : ""}
                  <code>{trace.correlationId}</code> · {trace.events.length} events
                </p>
              </div>
              <button type="button" className="trace-close" onClick={() => setTrace(null)} aria-label="Close trace">
                ✕
              </button>
            </div>
            <ol className="trace-events">
              {trace.events.map((event) => (
                <li className={`trace-event ${event.type.split(".")[0]}`} key={event.seq}>
                  <span className="trace-seq">{event.seq}</span>
                  <span className="trace-type">{event.type}</span>
                  <span className="trace-detail">{describeTraceEvent(event)}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function describeTraceEvent(event: TraceEvent): string {
  switch (event.type) {
    case "run.started":
      return `${event.name ?? "invoke"} · source=${event.source ?? "?"}${event.riskTier ? ` · risk=${event.riskTier}` : ""}`;
    case "tool.called":
      return `${event.name} → ${event.decision}${event.latencyMs != null ? ` · ${event.latencyMs}ms` : ""}`;
    case "agent.handoff":
      return `${event.name} (${event.status})${event.handoffTo ? ` → ${event.handoffTo}` : ""}`;
    case "policy.decision":
      return `decision = ${event.decision}`;
    case "run.completed":
      return `requiresHumanReview = ${event.requiresHumanReview}`;
    case "review.created":
      return `task ${event.status}`;
    case "review.transition":
      return `${event.action} by ${event.actor} → ${event.to}`;
    default:
      return "";
  }
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
