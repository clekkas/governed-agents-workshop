# RAG retrieval flow — grounded, cited, escalated

How the agent turns a case into a **cited, grounded** answer — or, when evidence is missing, a
**human-review escalation instead of a guess**. Grounded in
`agent-service/src/discharge_transition_agent/knowledge.py` (retrieval + diagnosis-scoping) and the
Evidence Retrieval / Care Plan / Human Review specialists. See the visual companion
`workshop-assets/rag-domain.svg` and the deck's Foundry IQ + RAG slide.

## The happy path and the escalation path

```mermaid
flowchart TD
    A[Evidence Retrieval Agent] --> B[Build query from the case<br/>diagnosis + transition keywords]
    B --> C[KnowledgeBase.retrieve<br/>score + diagnosis-scoping filter]
    C --> D{Required specialty<br/>protocol present?}
    D -- "yes: has_protocol_for(dx)" --> E[Top-k cited evidence<br/>claim-level + confidence band]
    E --> F[Care Plan Drafting Agent<br/>evidence packet BEFORE answer]
    F --> G[Human Review Agent<br/>draft + citations -> care manager]
    D -- "no: missing specialty doc" --> H[protocol.search = review_required]
    H --> I[Escalate to HITL<br/>Durable Task Scheduler]
    I --> G
    G --> J[Care manager approves / reworks / rejects]

    classDef stop fill:#fef2f2,stroke:#dc2626,color:#0f172a;
    classDef ok fill:#ecfdf5,stroke:#16a34a,color:#0f172a;
    class H,I stop;
    class E,F ok;
```

## As a sequence

```mermaid
sequenceDiagram
    participant Case
    participant ERA as Evidence Retrieval Agent
    participant KB as KnowledgeBase / Foundry IQ
    participant CPD as Care Plan Drafting
    participant HITL as Human Review (DTS)

    Case->>ERA: case (diagnosis, context)
    ERA->>KB: retrieve(query, diagnosis)
    Note over KB: diagnosis-scoping — a CHF protocol<br/>never surfaces for a COPD case
    alt specialty protocol present
        KB-->>ERA: top-k cited evidence (+confidence)
        ERA->>CPD: evidence packet (claims + citations)
        CPD->>HITL: drafted exception packet
    else required specialty protocol missing
        KB-->>ERA: review_required (no evidence)
        ERA->>HITL: escalate — do not guess
    end
    HITL-->>Case: care-manager decision (approve / rework / reject)
```

## Why this is the point (not a demo trick)

1. **Evidence packet before answer.** Retrieval runs first and produces claims + citations; the draft
   is written *from* that packet, not the model's memory.
2. **Diagnosis-scoping.** `knowledge.py` only lets a diagnosis-specific document surface for its own
   diagnosis (`_detect_specialty` + the scoping filter in `retrieve`), so a CHF protocol can't ground
   a COPD case.
3. **Missing evidence escalates.** When a required specialty protocol is absent
   (`has_protocol_for(dx)` is false), `protocol.search` returns `review_required` and the workflow
   routes to the human gate instead of proceeding on general guidance.
4. **Measured, not vibes.** The retrieval eval harness (`agent-service/eval/evaluate_retrieval.py`,
   `qrels.jsonl`) scores precision@k / recall@k / MRR and can gate on a minimum — measure retrieval
   *before* tuning prompts (the GPT-RAG accelerator pattern).
5. **Same contract on graduation.** Swapping the local `KnowledgeBase` for Foundry IQ / Azure AI
   Search keeps the `query -> cited evidence + coverage signal` contract, so the agents don't change.

## References

- `docs/rag-guidance-gpt-rag.md` · `docs/rag-development-patterns.md` · `docs/existing-vs-foundry-search.md`
- `docs/capability-host-reuse-and-cost.md` (reuse + cost on graduation)
- `workshop-assets/rag-domain.svg` (the RAG domain / pipeline diagram)
