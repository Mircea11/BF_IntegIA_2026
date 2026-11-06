#!/usr/bin/env python3
"""E17 — read-only benchmark of MMR against E11 retrieval metrics.

Run from RAG Hôpital project root after installing E17 pilot module:
  python scripts/benchmark_mmr_e17.py --limit 10
  python scripts/benchmark_mmr_e17.py --limit 100

Uses existing hopital_eval.json (100 in-corpus questions), the existing E17
MMR query, and the existing E11 reranker and metric functions. Qdrant is read
only, PostgreSQL is untouched, and no model for answer generation is required.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from time import perf_counter

from qdrant_client import QdrantClient

from rag_hopital.config import settings
from rag_hopital.etl.index import HYBRID_COLLECTION
from rag_hopital.evaluation.metrics import judge_chunk, evaluate_fact_coverage, ndcg_at_k
from rag_hopital.rag.search import search
from rag_hopital.rag.rerank import rerank_points
from experiment_mmr_e17 import search_hybrid_mmr, average_pairwise_jaccard

ARMS = (
    "rrf5", "mmr5", "rrf30_rerank5", "rrf15_rerank5", "mmr15_rerank5"
)


def evaluate_points(question: dict, points: list, k: int = 5) -> dict:
    """Match E11's evidence-unique nDCG and complete-answer Hit@5 rules."""
    points = points[:k]
    evidence_to_position = {id(e): pos for pos, e in enumerate(question["evidence"])}
    seen = set()
    grades = []
    matches_at_rank = []
    for point in points:
        payload = point.payload or {}
        text = payload.get('text', '')
        document = payload.get('document')
        if not isinstance(text,str) or not isinstance(document,str):
            raise ValueError('Missing text or document in Qdrant payload')
        matches = judge_chunk(question, document, text)
        matches_at_rank.append(matches)
        new_grades = []
        for evidence in matches:
            position = evidence_to_position[id(evidence)]
            if position not in seen:
                new_grades.append(evidence["grade"])
                seen.add(position)
        grades.append(max(new_grades, default=0))
    coverage = evaluate_fact_coverage(question, matches_at_rank, k=k)
    rank = coverage['first_complete_rank']
    score = ndcg_at_k(grades,[e['grade'] for e in question['evidence']],k=k)
    if not 0.0<=score<=1.000001:
        raise ValueError(f'nDCG outside [0,1] for {question["id"]}: {score}')
    return {
        'hit_at_5': int(rank is not None and rank <= k),
        'fact_recall_at_5': coverage['fact_recall'],
        'ndcg_at_5': score,
        'mean_jaccard': average_pairwise_jaccard(points),
        'returned':len(points),
        'chunks': [(p.payload or {}).get('chunk_id') for p in points],
        'first_complete_rank': rank,
    }


def summary(rows:list[dict]):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['arm']].append(row)
    out={}
    for arm in ARMS:
        r=grouped.get(arm,[])
        if not r:continue
        d={
            'questions':len(r),
            'hit_at_5':mean(x['hit_at_5'] for x in r),
            'fact_recall_at_5':mean(x['fact_recall_at_5'] for x in r),
            'ndcg_at_5':mean(x['ndcg_at_5'] for x in r),
            'mean_latency_seconds':mean(x['query_latency_seconds'] for x in r),
            'mean_jaccard':mean(x['mean_jaccard'] for x in r if x['mean_jaccard'] is not None) if any(x['mean_jaccard'] is not None for x in r) else None,
        }
        out[arm]=d
    return out


def select_questions(dataset: Path, limit: int | None, types: list[str]) -> list[dict]:
    data=json.loads(dataset.read_text(encoding='utf-8'))
    all_types=sorted({q['type'] for q in data})
    if any(t not in all_types for t in types):
        raise ValueError('Unknown type. Valid: '+', '.join(all_types))
    selected=[q for q in data if q['type']!='out_of_corpus' and (not types or q['type'] in types)]
    if not types and len(selected)!=100:
        raise ValueError(f'Expected 100 answerable questions, found {len(selected)}')
    return selected[:limit] if limit is not None else selected


def run_question(question,candidates,pool,diversity,rerank):
    """Search same full 30-candidate RRF set for A and B; MMR diversifies C.
    First two arms are RRF5 and MMR5 with no reranker.
    """
    prompt=question['question']
    start=perf_counter()
    base=search(query=prompt,top_k=candidates,method='hybrid',candidates=candidates,rerank=False)
    base_seconds=perf_counter()-start
    start=perf_counter()
    mmr=search_hybrid_mmr(query=prompt, top_k=pool,candidates=candidates,
                          mmr_pool=pool,diversity=diversity,patient_ipp=None,rerank=False)
    mmr_seconds=perf_counter()-start
    arms={
        'rrf5': (base[:5],base_seconds),
        'mmr5': (mmr[:5],mmr_seconds),
    }
    if rerank:
        # All reranker arms use same existing CPU model, but different subsets.
        for name, points, elapsed in [
            ('rrf30_rerank5',base[:candidates],base_seconds),
            ('rrf15_rerank5',base[:pool],base_seconds),
            ('mmr15_rerank5',mmr[:pool],mmr_seconds),
        ]:
            start=perf_counter()
            ranked=rerank_points(prompt,points,top_k=5)
            arms[name]=(ranked,elapsed+perf_counter()-start)
    return arms


def render_md(meta, agg, rows):
    lines=[
        '# E17 — MMR vs RRF : benchmark lecture seule', '',
        f"Date (UTC) : {meta['timestamp_utc']}",
        f"Questions : {meta['question_count']} ; candidats RRF : {meta['candidates']} ; pool MMR : {meta['mmr_pool']} ; diversity : {meta['diversity']}",
        'Filtres patient : **désactivés pour toutes les stratégies**, conformément à la baseline E11.',
        'Les questions multi-patients et celles qui requièrent des notices ne sont donc pas exclues.',
        '',
        '## Moyennes (sur les questions exécutées)', '',
        '| Stratégie | Hit@5 | Fact Recall@5 | nDCG@5 | Jaccard entre résultats | Durée/question* |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for a,v in agg.items():
        jj='n/a' if v['mean_jaccard'] is None else f"{v['mean_jaccard']:.4f}"
        lines.append(f"| {a} | {v['hit_at_5']:.1%} | {v['fact_recall_at_5']:.1%} | {v['ndcg_at_5']:.1%} | {jj} | {v['mean_latency_seconds']:.2f} s |")
    lines += ['','*Durée par stratégie non strictement indépendante : recherches initiales partagées pour certaines stratégies ; ne pas comparer comme coût total de production.*',
      '', '## Méthodologie', '',
      '- Même jeu de questions et mêmes preuves de référence pour toutes les stratégies.',
      '- `rrf5` : cinq premiers de RRF ; `mmr5` : cinq premiers de MMR parmi les candidats RRF.',
      '- `rrf30_rerank5` : reranker tous les candidats RRF ; correspond à la logique E11.',
      '- `rrf15_rerank5` : reranker les premiers éléments RRF du même pool ; contrôle de taille.',
      '- `mmr15_rerank5` : reranker un sous-ensemble diversifié par MMR.',
      '- Hit@5 = tous les faits nécessaires présents ; nDCG à preuves uniques = convention E11 locale.',
      '- Les nombres 30/15 sont des valeurs paramétrables ; ne pas généraliser un résultat d’un petit pilote.',
      '- Requêtes Qdrant et fichiers source en lecture seule ; aucune écriture PostgreSQL.',
      '', '## Résultats par type de question', '',
      '| Type | Stratégie | N | Hit@5 | Fact Recall@5 | nDCG@5 |',
      '|---|---|---:|---:|---:|---:|',
    ]
    types=sorted({r['type'] for r in rows})
    for ty in types:
        for arm in agg:
            sub=[r for r in rows if r['type']==ty and r['arm']==arm]
            if not sub: continue
            lines.append(f"| {ty} | {arm} | {len(sub)} | {mean(x['hit_at_5'] for x in sub):.1%} | {mean(x['fact_recall_at_5'] for x in sub):.1%} | {mean(x['ndcg_at_5'] for x in sub):.1%} |")
    lines += ['', '## Précautions', '',
      '- La comparaison sur un petit échantillon ne démontre pas un gain généralisable.',
      '- MMR est appliqué aux candidats RRF et utilise les vecteurs dense pour diversifier.',
      '- Le filtre par patient doit faire l’objet d’une évaluation séparée : le filtre strict exclut les notices générales.',
      '- En cas de divergence avec les scores historiques E11, vérifier les versions du corpus, des index et du reranker.',
      '']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--limit',type=int,default=10,help='Questions à tester (défaut 10 ; 100 pour l’ensemble)')
    ap.add_argument('--type',action='append',default=[],help='Filtrer par type, répétable')
    ap.add_argument('--candidates',type=int,default=30)
    ap.add_argument('--mmr-pool',type=int,default=15)
    ap.add_argument('--diversity',type=float,default=0.6)
    ap.add_argument('--no-rerank',action='store_true',help='Exécuter seulement RRF5 et MMR5')
    ap.add_argument('--output-prefix',default='reports/mmr/E17_benchmark')
    args=ap.parse_args()
    if args.limit is not None and args.limit<1:
        ap.error('--limit doit être positif')
    if args.candidates<5 or not 5<=args.mmr_pool<=args.candidates:
        ap.error('require candidates >= mmr-pool >= 5')
    if not 0<=args.diversity<=1:
        ap.error('require diversity between 0 and 1')
    dataset=settings.corpus_path/'hopital_eval.json'
    questions=select_questions(dataset,args.limit,args.type)
    if not questions:
        ap.error('aucune question sélectionnée')
    client=QdrantClient(url=settings.qdrant_url,api_key=settings.qdrant_api_key or None)
    if not client.collection_exists(HYBRID_COLLECTION):
        raise RuntimeError(f'Collection absente: {HYBRID_COLLECTION}. Arrêt sans modification.')
    count=client.count(collection_name=HYBRID_COLLECTION,exact=True).count
    print(f'Collection {HYBRID_COLLECTION}: {count} points ; jeu de questions: {len(questions)}',flush=True)
    print('Filtre patient désactivé pour tous les bras (comparabilité E11).',flush=True)
    rows=[]
    for i,question in enumerate(questions,1):
        print(f"{i:03d}/{len(questions):03d} {question['id']} [{question['type']}]",flush=True)
        arms=run_question(question,args.candidates,args.mmr_pool,args.diversity,not args.no_rerank)
        for name,(points,secs) in arms.items():
            metric=evaluate_points(question,points)
            record={
                'id':question['id'],'type':question['type'],'arm':name,
                'question':question['question'],'patient_ipp':question.get('patient_ipp'),
                'query_latency_seconds':round(secs,4),**metric,
            }
            rows.append(record)
            print(f"  {name:17s} Hit@5={metric['hit_at_5']} FactRecall@5={metric['fact_recall_at_5']:.2f} nDCG@5={metric['ndcg_at_5']:.2f}",flush=True)
    prefix=Path(args.output_prefix)
    prefix.parent.mkdir(parents=True,exist_ok=True)
    meta={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
          'dataset':str(dataset),'collection':HYBRID_COLLECTION,'collection_points':count,
          'question_count':len(questions),'candidates':args.candidates,'mmr_pool':args.mmr_pool,
          'diversity':args.diversity,'rerank':not args.no_rerank,
          'patient_filter':'none (matches historical E11)' }
    agg=summary(rows)
    # Emit JSON with question details and separate CSV for easy review.
    (prefix.with_suffix('.json')).write_text(json.dumps({'meta':meta,'summary':agg,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with prefix.with_suffix('.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row,'chunks':' | '.join(row['chunks'])})
    (prefix.with_suffix('.md')).write_text(render_md(meta,agg,rows),encoding='utf-8')
    print('\n=== BENCHMARK ===')
    for name,a in agg.items():
        print(f"{name:17s} hit={a['hit_at_5']:.1%} recall={a['fact_recall_at_5']:.1%} nDCG={a['ndcg_at_5']:.1%}")
    print('Reports:', str(prefix)+'.md / .csv / .json')
    print('Aucun changement de collection Qdrant, PostgreSQL ou baseline E11.')


if __name__=='__main__':
    main()
