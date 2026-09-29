// API client for the discharge-transition backend. Falls back gracefully to
// sample data in App.tsx if the backend is unreachable, so the UI still runs
// offline during a workshop.

import type {
  AgentContribution,
  EvidenceItem,
  ReviewCase,
  RiskTier,
  ToolCall,
} from "./types";

export interface CaseSummary {
  id: string;
  patientLabel: string;
  facility: string;
  diagnosis: string;
  riskTier: RiskTier;
  summary: string;
}

interface ApiEvidence {
  source: string;
  citation: string;
  claim: string;
  confidence?: "High" | "Medium" | "Low";
}

interface ApiToolCall {
  name: string;
  decision: ToolCall["decision"];
  latencyMs: number;
}

interface ApiHandoff {
  agentName: string;
  role: string;
  status: AgentContribution["status"];
  summary: string;
  handoffTo?: string;
}

export interface InvokeResult {
  correlationId: string;
  caseId: string;
  summary: string;
  approvedRiskScore: { tier: RiskTier; score: number; provenance: string };
  transitionGaps: string[];
  missingInformation: string[];
  evidence: ApiEvidence[];
  draftExceptionPacket: string[];
  toolCalls: ApiToolCall[];
  agentHandoffs: ApiHandoff[];
  policyDecision: string;
  requiresHumanReview: boolean;
}

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`Request failed (${status}): ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    // Try to surface the backend's Problem+JSON detail; fall back to the status text.
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.title || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export async function fetchCases(): Promise<CaseSummary[]> {
  const data = await getJson<{ cases: CaseSummary[] }>("/api/v1/cases");
  return data.cases;
}

export async function invokeAgent(caseId: string): Promise<InvokeResult> {
  return getJson<InvokeResult>("/api/v1/agent/invoke", {
    method: "POST",
    body: JSON.stringify({ caseId, actorRole: "care-manager" }),
  });
}

// --- HITL review tasks (Data Task Scheduler approval gate) ---
export type TaskAction = "claim" | "approve" | "request_changes" | "reject" | "escalate" | "rework";

export interface TaskHistoryEntry {
  timestamp: string;
  from: string | null;
  to: string;
  action: string;
  actor: string;
  note: string;
}

export interface ReviewTask {
  taskId: string;
  correlationId: string;
  caseId: string;
  status: string;
  assignedRole?: string | null;
  policyDecision?: string;
  dueAt?: string;
  history: TaskHistoryEntry[];
}

// Send a care-manager decision to the durable review task. The backend enforces the state
// machine (illegal transitions -> 409, missing human actor on approve/reject -> 403).
export async function applyTaskAction(
  correlationId: string,
  action: TaskAction,
  actor = "care-manager",
  note = "",
): Promise<ReviewTask> {
  return getJson<ReviewTask>(`/api/v1/tasks/${encodeURIComponent(correlationId)}/action`, {
    method: "POST",
    body: JSON.stringify({ action, actor, note }),
  });
}

// Read the current durable review task (server truth) — used to re-sync the UI after an action.
export async function fetchTask(correlationId: string): Promise<ReviewTask> {
  return getJson<ReviewTask>(`/api/v1/tasks/${encodeURIComponent(correlationId)}`);
}

// --- Backend activity log (live observability preview) ---
export interface LogEntry {
  seq: number;
  timestamp: string;
  level: string;
  message: string;
  correlationId: string | null;
}

export async function fetchLogs(since = 0, limit = 100): Promise<{ logs: LogEntry[]; lastSeq: number }> {
  return getJson<{ logs: LogEntry[]; lastSeq: number }>(`/api/v1/logs?since=${since}&limit=${limit}`);
}

// Merge a case summary and its invoke result into the render model the UI uses.
export function toReviewCase(summary: CaseSummary, invoke: InvokeResult): ReviewCase {
  const evidence: EvidenceItem[] = invoke.evidence.map((item, index) => ({
    id: `E${index + 1}`,
    source: item.source,
    citation: item.citation,
    claim: item.claim,
    confidence: item.confidence ?? "Medium",
  }));

  const toolCalls: ToolCall[] = invoke.toolCalls.map((call, index) => ({
    id: `T${index + 1}`,
    name: call.name,
    decision: call.decision,
    latencyMs: call.latencyMs,
  }));

  const agentContributions: AgentContribution[] = invoke.agentHandoffs.map((agent, index) => ({
    id: `A${index + 1}`,
    agentName: agent.agentName,
    role: agent.role,
    status: agent.status,
    summary: agent.summary,
    handoffTo: agent.handoffTo,
  }));

  return {
    id: summary.id,
    patientLabel: summary.patientLabel,
    facility: summary.facility,
    diagnosis: summary.diagnosis,
    riskTier: invoke.approvedRiskScore.tier,
    riskScore: invoke.approvedRiskScore.score,
    riskScoreProvenance: invoke.approvedRiskScore.provenance,
    // Escalating policy decisions create the task already Escalated (terminal) on the server —
    // reflect that from the start so the action buttons render correctly.
    status: invoke.policyDecision === "escalate" ? "Escalated" : "PendingReview",
    due: invoke.policyDecision === "escalate" ? "Escalated to specialist" : "Pending review",
    summary: invoke.summary,
    riskDrivers: [
      `Approved risk tier: ${invoke.approvedRiskScore.tier}.`,
      "Score consumed from risk_score.get; not generated by the agent.",
    ],
    transitionGaps: invoke.transitionGaps,
    missingInformation: invoke.missingInformation,
    draftPlan: invoke.draftExceptionPacket,
    evidence,
    toolCalls,
    agentContributions,
    timeline: [
      {
        id: `${summary.id}-invoked`,
        label: `Workflow completed · policy: ${invoke.policyDecision}`,
        actor: "Discharge Transition Orchestrator",
        timestamp: "Now",
      },
    ],
    correlationId: invoke.correlationId,
  };
}
