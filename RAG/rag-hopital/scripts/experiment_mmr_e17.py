#!/usr/bin/env python3
"""RAG Hôpital E17 — read-only hybrid RRF vs RRF→MMR trial.

Run from project root with the existing venv:
  python scripts/experiment_mmr_e17.py --question 'Quelles sont les allergies médicamenteuses ?'
  python scripts/experiment_mmr_e17.py --question '...' --patient-ipp 4100001
  python scripts/experiment_mmr_e17.py --question '...' --rerank --mmr-pool 15

No points are inserted, changed or deleted. Does not invoke a generation LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean

from qdrant_client import models

from rag_hopital.etl.index import (
    HYBRID_COLLECTION,
    connect_hybrid_qdrant,
    embed_texts,
)
from rag_hopital.rag.search import embed_sparse_query, search
from rag_hopital.rag.rerank import rerank_points


def patient_filter_for(ipp: str | None):
    if ipp is None:
        return None
    ipp = str(ipp).strip()
    if not ipp:
        raise ValueError('patient_ipp cannot be empty')
    return models.Filter(
        must=[models.FieldCondition(
            key='patient_ipp',
            match=models.MatchValue(value=ipp),
        )]
    )


def search_hybrid_mmr(
    query: str,
    *,
    top_k: int = 5,
    candidates: int = 30,
    mmr_pool: int = 5,
    diversity: float = 0.6,
    patient_ipp: str | None = None,
    rerank: bool = False,
):
    """Dense + BM25 -> RRF(candidate pool) -> Qdrant MMR -> optional CPU reranker.

    If rerank=True, MMR selects an intermediate pool (e.g. 15) before CPU
    reranking selects the final top_k. This intentionally changes the pool
    relative to E11's 30-candidate reranking, and must be disclosed.
    """
    if not query.strip():
        raise ValueError('query cannot be empty')
    if top_k < 1 or candidates < top_k:
        raise ValueError('require candidates >= top_k >= 1')
    if not 0.0 <= diversity <= 1.0:
        raise ValueError('diversity must be between 0 and 1')
    if not top_k <= mmr_pool <= candidates:
        raise ValueError('require top_k <= mmr_pool <= candidates')
    if not hasattr(models, 'Mmr') or not hasattr(models, 'NearestQuery'):
        raise RuntimeError('qdrant-client does not expose models.Mmr / NearestQuery')

    filter_ = patient_filter_for(patient_ipp)
    dense_vector = embed_texts([query])[0]
    sparse_vector = embed_sparse_query(query)
    client = connect_hybrid_qdrant()

    # Filter on each retrieval branch AND outer query to prevent leakage.
    response = client.query_points(
        collection_name=HYBRID_COLLECTION,
        prefetch=models.Prefetch(
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using='dense',
                    limit=candidates,
                    filter=filter_,
                ),
                models.Prefetch(
                    query=sparse_vector,
                    using='bm25',
                    limit=candidates,
                    filter=filter_,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=candidates,
            filter=filter_,
        ),
        query=models.NearestQuery(
            nearest=dense_vector,
            mmr=models.Mmr(
                diversity=diversity,
                candidates_limit=candidates,
            ),
        ),
        using='dense',
        query_filter=filter_,
        limit=mmr_pool if rerank else top_k,
        with_payload=True,
    )
    points = response.points
    if rerank:
        points = rerank_points(question=query, points=points, top_k=top_k)
    return points


def shingles(text: str, k: int = 3) -> set[tuple[str, ...]]:
    """Simple lexical redundancy indicator; NOT semantic equivalence."""
    lines = text.splitlines()
    if lines and lines[0].strip().lower().startswith('patient:'):
        lines = lines[1:]
    text = unicodedata.normalize('NFKD', '\n'.join(lines).casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    words = re.findall(r'\w+', text)
    if len(words) < k:
        return set()
    return {tuple(words[i:i + k]) for i in range(len(words) - k + 1)}


def average_pairwise_jaccard(points) -> float | None:
    values = []
    for a, b in combinations(points, 2):
        sa = shingles(str((a.payload or {}).get('text') or ''))
        sb = shingles(str((b.payload or {}).get('text') or ''))
        if sa or sb:
            values.append(len(sa & sb) / len(sa | sb))
    return round(mean(values), 5) if values else None


def serialize_point(point) -> dict:
    payload = point.payload or {}
    return {
        'chunk_id': payload.get('chunk_id'),
        'document': payload.get('document'),
        'patient_ipp': payload.get('patient_ipp'),
        'score': float(point.score),
    }


def print_points(title: str, points):
    print('\n' + title)
    for i, p in enumerate(points, 1):
        x = serialize_point(p)
        print(f"{i}. patient={x['patient_ipp']} | chunk={x['chunk_id']} | score={x['score']:.5f}")
    print('Jaccard moyen entre résultats:', average_pairwise_jaccard(points))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', required=True)
    parser.add_argument('--patient-ipp', default=None)
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--candidates', type=int, default=30)
    parser.add_argument('--diversity', type=float, default=0.6)
    parser.add_argument('--mmr-pool', type=int, default=None,
                        help='MMR intermediate pool when --rerank, default 15')
    parser.add_argument('--rerank', action='store_true',
                        help='Compare E11 reranked vs MMR→CPU reranked')
    parser.add_argument('--output', default='reports/mmr/E17_pilot.json')
    args = parser.parse_args()

    pool = args.mmr_pool if args.mmr_pool is not None else (15 if args.rerank else args.top_k)
    if not args.rerank and pool != args.top_k:
        parser.error('--mmr-pool must equal --top-k unless --rerank is enabled')
    if args.patient_ipp is not None and not args.patient_ipp.strip():
        parser.error('--patient-ipp cannot be empty')

    print('E17 READ-ONLY | hybrid RRF vs hybrid RRF + MMR')
    print(f'patient={args.patient_ipp or "none"} | candidates={args.candidates} | diversity={args.diversity} | rerank={args.rerank}')
    print('MMR diversity 0=relevance, 1=maximum diversity (Qdrant convention).')

    baseline = search(
        query=args.question, method='hybrid', top_k=args.top_k,
        candidates=args.candidates, patient_ipp=args.patient_ipp,
        rerank=args.rerank,
    )
    trial = search_hybrid_mmr(
        args.question, top_k=args.top_k, candidates=args.candidates,
        mmr_pool=pool, diversity=args.diversity,
        patient_ipp=args.patient_ipp, rerank=args.rerank,
    )
    print_points('A. BASELINE HYBRID' + (' + RERANK' if args.rerank else ''), baseline)
    print_points('B. HYBRID + MMR' + (' + RERANK' if args.rerank else ''), trial)
    if args.patient_ipp is not None:
        # A nonempty response also required to avoid vacuous success on [].
        for label, points in [('baseline', baseline), ('MMR', trial)]:
            if not points:
                print(f'ATTENTION: {label} has zero results for patient {args.patient_ipp}')
            if any(str((p.payload or {}).get('patient_ipp')) != args.patient_ipp for p in points):
                raise AssertionError(f'{label} returned another patient')

    baseline_ids = {x['chunk_id'] for x in map(serialize_point, baseline)}
    mmr_ids = {x['chunk_id'] for x in map(serialize_point, trial)}
    common = baseline_ids & mmr_ids
    print(f'\nTop-{args.top_k} overlap: {len(common)} shared chunks')
    print('A only:', sorted(baseline_ids - mmr_ids))
    print('B only:', sorted(mmr_ids - baseline_ids))
    print('NOTE: baseline and MMR scores are not directly comparable.')

    result = {
        'experiment': 'E17 pilot',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'question': args.question,
        'patient_ipp': args.patient_ipp,
        'candidates_per_branch': args.candidates,
        'top_k': args.top_k,
        'mmr_pool': pool,
        'diversity': args.diversity,
        'rerank': args.rerank,
        'baseline': list(map(serialize_point, baseline)),
        'mmr': list(map(serialize_point, trial)),
        'baseline_mean_pairwise_trigram_jaccard': average_pairwise_jaccard(baseline),
        'mmr_mean_pairwise_trigram_jaccard': average_pairwise_jaccard(trial),
        'top_k_overlap': len(common),
    }
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Result file:', dest)
    print('No modifications to Qdrant collections or E11 configurations.')


if __name__ == '__main__':
    main()
