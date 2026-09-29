"""Retrieval evaluation harness — the GPT-RAG 'measure retrieval before you tune' pattern, locally.

Reads labeled relevance judgments (qrels.jsonl, rubric 0-4) and scores the local KnowledgeBase
retrieval with precision@k, recall@k, and MRR. A relevant document is label >= 2 (partially
relevant or better), matching the accelerator's rubric.

This is a miniature of the accelerator's method: fixed corpus + fixed questions + a split (tune vs
held_out) + qrels + normalized metrics. Graduate it to Foundry IQ by swapping the retriever.

Run:  python eval/evaluate_retrieval.py            (tune split, default)
      python eval/evaluate_retrieval.py --split held_out
      python eval/evaluate_retrieval.py --k 3 --min-precision 0.5   (gate)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discharge_transition_agent.knowledge import KnowledgeBase  # noqa: E402

RELEVANT_THRESHOLD = 2  # label >= 2 counts as relevant (partial or better)


def load_qrels(path: Path, split: str | None) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if split is None or row.get("split") == split:
            rows.append(row)
    return rows


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    hits = sum(1 for c in top if c in relevant)
    return hits / len(top)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    top = set(retrieved[:k])
    return len(top & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for i, c in enumerate(retrieved, start=1):
        if c in relevant:
            return 1.0 / i
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="tune", choices=["tune", "held_out", "all"])
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--min-precision", type=float, default=0.0, help="Gate: fail if mean precision@k is below this.")
    args = parser.parse_args()

    qrels_path = Path(__file__).resolve().parent / "qrels.jsonl"
    split = None if args.split == "all" else args.split
    rows = load_qrels(qrels_path, split)
    if not rows:
        print(f"No qrels for split '{args.split}'.")
        return 1

    kb = KnowledgeBase()
    print(f"Corpus: {len(kb.docs)} docs from {kb.docs_dir}")
    print(f"Split: {args.split}   k={args.k}   relevant = label >= {RELEVANT_THRESHOLD}\n")

    p_sum = r_sum = mrr_sum = 0.0
    header = f"{'question':<22}{'P@k':>7}{'R@k':>7}{'RR':>7}"
    print(header)
    print("-" * len(header))
    for row in rows:
        relevant = {c for c, label in row["labels"].items() if label >= RELEVANT_THRESHOLD}
        results = kb.retrieve(row["query"], diagnosis=row.get("diagnosis"), k=args.k)
        retrieved = [e["citation"] for e in results]
        p = precision_at_k(retrieved, relevant, args.k)
        r = recall_at_k(retrieved, relevant, args.k)
        rr = reciprocal_rank(retrieved, relevant)
        p_sum += p
        r_sum += r
        mrr_sum += rr
        print(f"{row['id']:<22}{p:>7.2f}{r:>7.2f}{rr:>7.2f}")

    n = len(rows)
    mean_p, mean_r, mrr = p_sum / n, r_sum / n, mrr_sum / n
    print("-" * len(header))
    print(f"{'MEAN':<22}{mean_p:>7.2f}{mean_r:>7.2f}{mrr:>7.2f}")

    if args.min_precision > 0 and mean_p < args.min_precision:
        print(f"\nGATE FAILED: mean P@{args.k} {mean_p:.2f} < {args.min_precision:.2f}")
        return 1
    print("\nRetrieval evaluation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
