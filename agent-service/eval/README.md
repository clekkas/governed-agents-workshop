# Retrieval evaluation

Applies the Azure GPT-RAG accelerator's **"measure retrieval before you tune"** pattern locally
(see `docs/rag-guidance-gpt-rag.md`).

- `qrels.jsonl` — labeled relevance judgments over the synthetic corpus in `data/rag-docs/`.
  Rubric: `4` fully answers, `3` strongly relevant, `2` partially relevant, `1` weakly related,
  `0` not relevant. A `split` of `tune` or `held_out` keeps evaluation honest — only open
  `held_out` after choosing a configuration.
- `evaluate_retrieval.py` — scores the local `KnowledgeBase` with precision@k, recall@k, and MRR.
  A document counts as relevant at label `>= 2`.

## Run

```powershell
cd agent-service
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split tune --k 3
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split held_out --k 3
# gate example (fail if mean precision@3 < 0.6):
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split tune --k 3 --min-precision 0.6
```

## Graduating to Foundry IQ

Keep the qrels and metrics; swap the retriever from the local `KnowledgeBase` to a Foundry IQ
knowledge base call. Measure each backend on its own identifiers and qrels — never compare raw
backend scores. Freeze the corpus, questions, identity/permissions, strategy, model, and document
limit across runs, and treat completed runs as immutable.
