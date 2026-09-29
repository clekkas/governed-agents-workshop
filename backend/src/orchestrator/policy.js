// Policy / guardrail enforcement module (WI-03).
//
// Extracts the guardrail decisions from the orchestrator into one reusable, testable place, encoding
// the matrix in policy/guardrail-test-matrix.md. Two layers:
//
//   1. Request/output guardrails — given candidate text (a requested action or a drafted line),
//      detect prohibited claims, order/medication changes, HITL bypass, and prompt injection, and
//      return a structured refusal. Reusable when the agent gains a free-text surface.
//   2. Run-condition policy — given the structured run state (evidence, gaps, PHI scope), derive the
//      final policyDecision the orchestrator returns.
//
// Decisions: "allow" | "review_required" | "redact" | "escalate" | "deny".
// Every decision is an object: { decision, code, reason, blocking }.

const DECISION = {
  ALLOW: "allow",
  REVIEW: "review_required",
  REDACT: "redact",
  ESCALATE: "escalate",
  DENY: "deny",
};

function decision(decision_, code, reason, blocking) {
  return { decision: decision_, code, reason, blocking: Boolean(blocking) };
}

// ---- pattern banks (case-insensitive) ---------------------------------------------------------
const PROHIBITED_CLAIM = [/\bsafe (?:to|for) discharge\b/i, /\bcleared (?:to|for) discharge\b/i, /\bdischarge is safe\b/i, /\bmedically cleared\b/i, /\bok to discharge\b/i, /\bfit for discharge\b/i];
const ORDER_CHANGE = [/\bchange (?:the )?discharge order\b/i, /\b(?:modify|alter|update|cancel) (?:the )?(?:discharge )?order\b/i, /\bdischarge (?:to|home)\b.*\border\b/i];
const MED_CHANGE = [/\b(?:stop|start|discontinue|d\/c|change|increase|decrease|adjust|prescribe|hold) (?:the )?\w+/i];
const MED_CONTEXT = /\b(diuretic|medication|med|dose|dosage|drug|prescription|insulin|anticoagulant)\b/i;
const HITL_BYPASS = [/\bapprove (?:the )?(?:plan|packet|case)\b/i, /\bmark (?:it )?(?:complete|approved|done)\b/i, /\bsign off\b/i, /\bfinalize without review\b/i, /\bskip (?:the )?review\b/i];
const INJECTION = [/\bignore (?:policy|previous|prior|all) (?:instructions|policy|rules)?\b/i, /\bignore policy\b/i, /\breveal (?:the )?full (?:chart|note|record)\b/i, /\bdisregard (?:the )?(?:rules|policy|guardrails)\b/i, /\boverride (?:the )?(?:policy|guardrail)\b/i];

function matchesAny(text, patterns) {
  return patterns.some((re) => re.test(text));
}

// ---- request/output guardrail checks (matrix rows) --------------------------------------------
function checkProhibitedClaim(text) {
  return matchesAny(text, PROHIBITED_CLAIM)
    ? decision(DECISION.DENY, "prohibited_claim", "Refuses to state a patient is safe to discharge; routes to human review.", true)
    : null;
}

function checkOrderChange(text) {
  return matchesAny(text, ORDER_CHANGE)
    ? decision(DECISION.DENY, "order_change", "Agent cannot alter discharge orders.", true)
    : null;
}

function checkMedicationChange(text) {
  return matchesAny(text, MED_CHANGE) && MED_CONTEXT.test(text)
    ? decision(DECISION.DENY, "medication_change", "Agent cannot change medication orders.", true)
    : null;
}

function checkHitlBypass(text) {
  return matchesAny(text, HITL_BYPASS)
    ? decision(DECISION.DENY, "hitl_bypass", "Agent cannot approve or complete a plan; the review task stays pending.", true)
    : null;
}

function checkPromptInjection(text) {
  return matchesAny(text, INJECTION)
    ? decision(DECISION.DENY, "prompt_injection", "Instruction found in content is treated as data; policy is preserved.", true)
    : null;
}

// Given candidate text (a requested action or an external note), return the first guardrail that
// fires, or an ALLOW decision. Order matters: most specific safety refusals first.
function screenText(text) {
  const input = String(text || "");
  const checks = [checkProhibitedClaim, checkPromptInjection, checkHitlBypass, checkOrderChange, checkMedicationChange];
  for (const check of checks) {
    const hit = check(input);
    if (hit) return hit;
  }
  return decision(DECISION.ALLOW, "allowed", "No prohibited content detected.", false);
}

// ---- run-condition checks ----------------------------------------------------------------------
// Missing citation: a protocol claim without a source requires a citation or missing-info disclosure.
function checkCitationRequired({ evidence = [], missingInformation = [] } = {}) {
  if (evidence.length === 0 && missingInformation.length === 0) {
    return decision(DECISION.REVIEW, "missing_citation", "Protocol output must cite a source or disclose missing evidence.", true);
  }
  return null;
}

// Full note request without explicit logged scope -> redact/deny.
function checkPhiScope({ requestFullNotes = false, hasLoggedScope = false } = {}) {
  if (requestFullNotes && !hasLoggedScope) {
    return decision(DECISION.REDACT, "phi_scope", "Full notes require an explicit logged scope; return redacted excerpt or deny.", true);
  }
  return null;
}

// Conflicting or missing/blocked evidence -> escalate to human review.
function checkEvidenceConflict({ evidenceBlocked = false, conflictingEvidence = false } = {}) {
  if (evidenceBlocked || conflictingEvidence) {
    return decision(DECISION.ESCALATE, "evidence_conflict", "Missing or conflicting evidence must escalate to human review.", true);
  }
  return null;
}

/**
 * Derive the run's overall policy decision from its structured state. This is what the orchestrator
 * returns. Order of precedence: escalate (blocked/conflicting) > redact (PHI scope) > review_required
 * (gaps or missing citation) > allow.
 * @returns {{decision, code, reason, blocking}}
 */
function decide(run = {}) {
  const {
    evidence = [],
    missingInformation = [],
    transitionGaps = [],
    evidenceBlocked = false,
    conflictingEvidence = false,
    requestFullNotes = false,
    hasLoggedScope = false,
  } = run;

  return (
    checkEvidenceConflict({ evidenceBlocked, conflictingEvidence }) ||
    checkPhiScope({ requestFullNotes, hasLoggedScope }) ||
    checkCitationRequired({ evidence, missingInformation }) ||
    (transitionGaps.length > 0
      ? decision(DECISION.REVIEW, "transition_gaps", "Open transition gaps require care-manager review before use.", true)
      : decision(DECISION.ALLOW, "allowed", "Grounded draft with no blocking conditions; still requires human review.", false))
  );
}

module.exports = {
  DECISION,
  decide,
  screenText,
  checkProhibitedClaim,
  checkOrderChange,
  checkMedicationChange,
  checkHitlBypass,
  checkPromptInjection,
  checkCitationRequired,
  checkPhiScope,
  checkEvidenceConflict,
};
