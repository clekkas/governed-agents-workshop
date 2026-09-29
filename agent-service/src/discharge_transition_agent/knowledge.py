"""Local knowledge base for RAG retrieval over approved protocol docs.

Reads the synthetic Markdown protocols in data/rag-docs and does lightweight keyword
retrieval so the Evidence Retrieval Agent grounds answers in real files with claim-level
citations. This is the local stand-in for Foundry IQ / Azure AI Search; the retrieval
contract (query -> cited evidence + coverage signal) is the same one a cloud knowledge
base fulfills, so the agents do not change when it moves to Foundry IQ.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "may", "are", "was", "should",
    "have", "has", "into", "onto", "per", "not", "but", "you", "your", "its", "their",
    "a", "an", "of", "to", "in", "on", "or", "is", "be", "by", "as", "at", "it",
    "synthetic", "workshop", "use", "only", "agent", "must", "plan", "planning",
}

# Diagnosis aliases so a specialty-protocol lookup is robust to naming.
_DIAGNOSIS_ALIASES = {
    "chf": ["chf", "heart failure", "congestive"],
    "copd": ["copd", "chronic obstructive"],
    "pneumonia": ["pneumonia"],
}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) >= 3 and w not in _STOPWORDS]


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return fallback.replace("_", " ").title()


def _sentences(text: str) -> list[str]:
    # Drop headings and metadata lines; split body into sentences.
    body = " ".join(
        ln.strip() for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    )
    parts = re.split(r"(?<=[.!?])\s+", body)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _docs_dir() -> Path:
    override = os.environ.get("RAG_DOCS_DIR", "").strip()
    if override:
        return Path(override)
    # knowledge.py -> discharge_transition_agent -> src -> agent-service -> repo root
    return Path(__file__).resolve().parents[3] / "data" / "rag-docs"


class KnowledgeBase:
    def __init__(self, docs_dir: str | Path | None = None) -> None:
        self.docs: list[dict[str, Any]] = []
        directory = Path(docs_dir) if docs_dir else _docs_dir()
        self.docs_dir = str(directory)
        if directory.exists():
            for f in sorted(directory.glob("*.md")):
                text = f.read_text(encoding="utf-8")
                self.docs.append(
                    {
                        "title": _title(text, f.stem),
                        "citation": f"rag-docs/{f.name}",
                        "filename": f.name.lower(),
                        "specialty": self._detect_specialty(f.name.lower(), _title(text, f.stem).lower()),
                        "text": text,
                        "tokens": _tokens(text),
                        "sentences": _sentences(text),
                    }
                )

    @staticmethod
    def _detect_specialty(filename: str, title: str) -> str | None:
        """Return the diagnosis a doc is specific to, or None if it is general guidance."""
        hay = f"{filename} {title}"
        for key, aliases in _DIAGNOSIS_ALIASES.items():
            if any(a in hay for a in aliases):
                return key
        return None

    def _best_sentence(self, doc: dict[str, Any], query_terms: set[str]) -> str:
        best, best_score = "", -1
        for s in doc["sentences"]:
            score = sum(1 for t in _tokens(s) if t in query_terms)
            if score > best_score:
                best, best_score = s, score
        return best or (doc["sentences"][0] if doc["sentences"] else doc["title"])

    def retrieve(self, query: str, diagnosis: str | None = None, k: int = 3) -> list[dict[str, Any]]:
        """Return up to k cited evidence items relevant to the query.

        Diagnosis-specific documents are only eligible for their own diagnosis, so a CHF
        protocol never surfaces for a COPD or pneumonia case. General guidance is always eligible.
        """
        q = set(_tokens(query))
        dx = diagnosis.lower() if diagnosis else None
        scored: list[tuple[int, dict[str, Any]]] = []
        for doc in self.docs:
            if doc["specialty"] is not None and doc["specialty"] != dx:
                continue  # specialty doc for a different diagnosis
            score = sum(1 for t in doc["tokens"] if t in q)
            # Boost the matching diagnosis-specific protocol so it ranks first.
            if doc["specialty"] is not None and doc["specialty"] == dx:
                score += 3
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, doc in scored[:k]:
            confidence = "High" if score >= 5 else "Medium" if score >= 3 else "Low"
            results.append(
                {
                    "source": doc["title"],
                    "citation": doc["citation"],
                    "claim": self._best_sentence(doc, q),
                    "confidence": confidence,
                }
            )
        return results

    def has_protocol_for(self, diagnosis: str) -> bool:
        """Whether a diagnosis-specific protocol document exists in the corpus."""
        keys = _DIAGNOSIS_ALIASES.get(diagnosis.lower(), [diagnosis.lower()])
        for doc in self.docs:
            hay = f"{doc['filename']} {doc['title'].lower()}"
            if any(k in hay for k in keys):
                return True
        return False
