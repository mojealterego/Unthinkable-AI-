"""Auditable page-boundary ranking for Cain's Jawbone (no solution claims).

Adapted from the user's 11-page PDF. Heuristic scores are NOT probabilities.
Full copyrighted book text must be imported by the user; it is not bundled here.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

_TERMINAL = re.compile(r"""[.!?][”"'’)\]]*\s*$""")
_WORD = re.compile(r"\b[^\W\d_]+(?:['’][^\W\d_]+)?\b", re.UNICODE)
_LEADING = re.compile(r"""^[\s"'“”‘’([{}\u2014\-]+""")
_STOP = frozenset({"the", "and", "that", "with", "from", "this", "then", "was", "were", "you", "your", "for", "but"})


@dataclass(frozen=True)
class BoundaryCandidate:
    from_page: int
    to_page: int
    heuristic_score: float
    evidence: tuple[str, ...]

    def json_dict(self) -> dict:
        return {**asdict(self), "evidence": list(self.evidence)}


@dataclass(frozen=True)
class StyleFeatures:
    page: int
    token_count: int
    type_token_ratio: float
    average_word_length: float
    punctuation_density: float


def normalize_pages(raw: Mapping[object, object], *, require_complete: bool = False) -> dict[int, str]:
    if not isinstance(raw, Mapping):
        raise TypeError("Expected a mapping of page number to text")
    pages: dict[int, str] = {}
    for k, value in raw.items():
        if isinstance(k, bool) or not str(k).isdigit() or not (1 <= int(k) <= 100):
            raise ValueError(f"Invalid page number: {k!r}")
        number = int(k)
        if number in pages:
            raise ValueError(f"Duplicate page number: {number}")
        if not isinstance(value, str) or not value.strip() or len(value) > 100_000:
            raise ValueError(f"Missing, oversize or invalid content for page {number}")
        pages[number] = value.strip()
    if len(pages) > 100:
        raise ValueError("At most 100 pages are supported")
    if require_complete and set(pages) != set(range(1, 101)):
        raise ValueError("A complete 100-page source is required for this operation")
    return dict(sorted(pages.items()))


def words(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD.finditer(text)]


def feature_vector(page_number: int, text: str) -> StyleFeatures:
    tokens = words(text)
    return StyleFeatures(
        page=page_number, token_count=len(tokens),
        type_token_ratio=len(set(tokens)) / len(tokens) if tokens else 0.0,
        average_word_length=sum(map(len, tokens)) / len(tokens) if tokens else 0.0,
        punctuation_density=sum(not (c.isalnum() or c.isspace()) for c in text) / len(text) if text else 0.0,
    )


def transition(a_page: int, a: str, b_page: int, b: str) -> BoundaryCandidate:
    if a_page == b_page:
        raise ValueError("Page cannot follow itself")
    a = a.strip()
    b = b.strip()
    if not a or not b:
        raise ValueError("Empty pages are not allowed")
    ends_with_sentence = bool(_TERMINAL.search(a))
    lead = _LEADING.sub("", b)
    starts_lower = bool(lead) and lead[0].islower()
    evidence: list[str] = []
    score = 0.0

    if not ends_with_sentence and starts_lower:
        score += 0.65
        evidence.append("incomplete_end_followed_by_lowercase")
    elif ends_with_sentence and not starts_lower:
        score += 0.15
        evidence.append("sentence_end_followed_by_uppercase_or_symbol")
    elif not ends_with_sentence and not starts_lower:
        evidence.append("incomplete_end_uppercase_conflict")
    else:
        score += 0.03
        evidence.append("sentence_end_lowercase_conflict")

    tail = set(words(a[-180:])) - _STOP
    head = set(words(b[:180])) - _STOP
    overlap = tail & head
    if overlap:
        score += min(0.20, 0.04 * len(overlap))
        evidence.append("boundary_lexical_overlap")

    # A lexical/syntactic ranking aid only: never present score as calibrated P(A->B).
    return BoundaryCandidate(a_page, b_page, round(min(1.0, max(0.0, score)), 3), tuple(evidence))


def candidate_transitions(pages: Mapping[object, object], *, top: int = 5) -> list[BoundaryCandidate]:
    valid = normalize_pages(pages)
    if not (1 <= top <= 99):
        raise ValueError("top must be 1..99")
    pairs: list[BoundaryCandidate] = []
    for a_id, a in valid.items():
        sorted_candidates = sorted(
            (transition(a_id, a, b_id, b) for b_id, b in valid.items() if b_id != a_id),
            key=lambda x: (-x.heuristic_score, x.to_page),
        )
        pairs.extend(sorted_candidates[:top])
    return pairs


def narrator_clusters(pages: Mapping[object, object], n_clusters: int = 6) -> dict[int, list[int]]:
    """Optional unsupervised exploration. Cluster labels do not identify true narrators.

    Requires: pip install scikit-learn numpy. No fitting data included.
    """
    valid = normalize_pages(pages)
    if n_clusters < 2 or n_clusters > len(valid):
        raise ValueError("n_clusters must be 2..number_of_pages")
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    pages_order = list(valid)
    contents = [valid[i] for i in pages_order]
    tfidf = TfidfVectorizer(max_features=1000, ngram_range=(1, 2)).fit_transform(contents)
    features = [feature_vector(i, valid[i]) for i in pages_order]
    numeric = np.array([[f.type_token_ratio, f.average_word_length, f.punctuation_density] for f in features])
    # Sparse text and dense numeric have distinct scales; tune only on a held-out labelled dataset.
    matrix = np.hstack([tfidf.toarray(), StandardScaler().fit_transform(numeric)])
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(matrix)
    return {label: [pages_order[i] for i, val in enumerate(labels) if val == label] for label in range(n_clusters)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="JSON mapping page numbers 1..100 to full text")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    raw = json.loads(args.corpus.read_text(encoding="utf-8"))
    pages = normalize_pages(raw, require_complete=args.require_complete)
    payload = {
        "method": "non-probabilistic-boundary-ranking-v1",
        "complete": len(pages) == 100,
        "page_count": len(pages),
        "candidates": [x.json_dict() for x in candidate_transitions(pages, top=args.top)],
        "style_features": [asdict(feature_vector(n, t)) for n, t in pages.items()],
        "solved": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
