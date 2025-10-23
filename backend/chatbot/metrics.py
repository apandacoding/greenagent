from __future__ import annotations
from math import log2
from typing import Dict, Iterable, List, Sequence, Tuple, Optional
import random


def dcg_at_k(relevances: Sequence[float], k: int) -> float:
    """Compute Discounted Cumulative Gain at K given a list of graded relevances."""
    k = max(0, int(k))
    if k == 0 or not relevances:
        return 0.0
    s = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        s += (2.0**rel - 1.0) / log2(i + 1.0)
    return s


def ndcg_at_k(ranked_ids: Sequence[str], relevance_map: Dict[str, float], k: int) -> float:
    """Compute NDCG@K given a ranked list of ids and a {id -> graded relevance} map."""
    if not ranked_ids or k <= 0:
        return 0.0
    rels = [float(relevance_map.get(i, 0.0)) for i in ranked_ids]
    dcg = dcg_at_k(rels, k)

    ideal = sorted(relevance_map.values(), reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def deterministic_tiebreak(items: List[Tuple[str, float]], seed: Optional[int] = None) -> List[Tuple[str, float]]:
    """
    Deterministically break ties by (score desc, stable shuffle by seed, id asc).
    Each item is (id, score).
    """
    rnd = random.Random(seed)
    shuffled = items[:]
    rnd.shuffle(shuffled)
    return sorted(shuffled, key=lambda x: (-x[1], x[0]))


def evaluate_ndcg_submission(
    submission_ranked: List[Tuple[str, float]],
    truth_relevance: Dict[str, float],
    ks: Iterable[int] = (1, 3, 5, 10),
    seed: Optional[int] = None,
) -> Dict[str, float]:
    """
    - submission_ranked: list of (listing_id, score) predicted by the white agent
    - truth_relevance: dict listing_id -> graded relevance (0..3 or 0..5 etc.)
    """
    ranked = deterministic_tiebreak(submission_ranked, seed=seed)
    ids_only = [i for i, _ in ranked]
    out: Dict[str, float] = {}
    for k in ks:
        out[f"ndcg@{k}"] = ndcg_at_k(ids_only, truth_relevance, k)
    return out
