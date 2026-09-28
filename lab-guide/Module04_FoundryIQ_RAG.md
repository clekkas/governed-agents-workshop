# Module 04: Foundry IQ and RAG

## Objective

Design a RAG pattern that combines structured Fabric data with approved protocol documents.

## RAG contract

1. Use approved source documents only.
2. Preserve source metadata.
3. Cite evidence for material claims.
4. Surface missing or conflicting evidence.
5. Route uncertain outputs to human review.

## Output

RAG architecture, source inventory, metadata model, and evaluation plan.

## Developer onboarding pattern

Teach RAG as a five-step development loop:

1. Source: identify approved documents and owners.
2. Index: chunk, embed, extract metadata, and preserve citations.
3. Retrieve: use keyword, vector, hybrid, or agentic retrieval.
4. Ground: build an evidence packet before answer generation.
5. Evaluate: test retrieval, groundedness, missing evidence, citations, and regression.

## Multi-surface discussion

The same grounded knowledge capability can appear in multiple Microsoft AI surfaces:

1. Foundry Agent Service: the core code-first or prompt-agent implementation.
2. Copilot Studio: a business-facing agent can connect to a Foundry agent.
3. Teams and Microsoft 365 Copilot: a Copilot Studio agent can be published to these channels after authentication, testing, and admin controls are configured.
4. Custom app: a care-manager application can call a Foundry agent endpoint or knowledge base API directly.

## Hands-on exercise

1. Pick one synthetic RAG document in `data/rag-docs`.
2. Define required metadata: source, owner, effective date, sensitivity, and citation URI.
3. Create an evidence packet for a readmissions planning question.
4. Produce an answer that uses only that evidence.
5. Repeat with a missing protocol and verify the agent says what is missing instead of guessing.
