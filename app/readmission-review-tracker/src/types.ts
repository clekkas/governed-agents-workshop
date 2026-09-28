export type RiskTier = "Critical" | "High" | "Medium" | "Low";

export type ReviewStatus =
  | "PendingReview"
  | "InReview"
  | "Approved"
  | "NeedsRework"
  | "Rejected";

export type PolicyDecision = "allow" | "redact" | "review_required" | "deny";

export interface EvidenceItem {
  id: string;
  source: string;
  citation: string;
  claim: string;
  confidence: "High" | "Medium" | "Low";
}

export interface ToolCall {
  id: string;
  name: string;
  decision: PolicyDecision;
  latencyMs: number;
}

export interface ReviewEvent {
  id: string;
  label: string;
  actor: string;
  timestamp: string;
}

export interface AgentContribution {
  id: string;
  agentName: string;
  role: string;
  status: "completed" | "needs-review" | "blocked";
  summary: string;
  handoffTo?: string;
}

export interface ReviewCase {
  id: string;
  patientLabel: string;
  facility: string;
  diagnosis: string;
  riskTier: RiskTier;
  riskScore: number;
  riskScoreProvenance: string;
  status: ReviewStatus;
  due: string;
  summary: string;
  riskDrivers: string[];
  transitionGaps: string[];
  missingInformation: string[];
  draftPlan: string[];
  evidence: EvidenceItem[];
  toolCalls: ToolCall[];
  agentContributions: AgentContribution[];
  timeline: ReviewEvent[];
  correlationId: string;
}
