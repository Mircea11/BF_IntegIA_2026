# E17 — Benchmark MMR sur le jeu d’évaluation RAG Hôpital

## Conditions
- Installer d'abord `rag_hopital_E17_MMR_trial.zip` : `scripts/experiment_mmr_e17.py` est requis.
- Activer `.venv`; démarrer Qdrant RAG Hôpital et BGE-M3 sur le serveur embeddings configuré (8101 dans la session).
- Le reranker E11 (`BAAI/bge-reranker-v2-m3`) est chargé localement sur CPU.
- Ne pas redémarrer HelpDesk-Ops ; ne pas lancer Qwen 9B (pas de génération).
- Le script lit `data/hopital/hopital_eval.json` (100 questions answerable, six hors corpus exclues).
- Ne modifie pas Qdrant, PostgreSQL, `search.py`, l'expérience E11, ni les index.

## Installer
```bash
cd ~/formation/RAG/rag-hopital
source .venv/bin/activate
unzip -n ~/Downloads/rag_hopital_E17_MMR_benchmark.zip -d .
python -m py_compile scripts/benchmark_mmr_e17.py
```

## Premier test (10 questions représentatives dans l'ordre du dataset)
```bash
python scripts/benchmark_mmr_e17.py --limit 10 --output-prefix reports/mmr/E17_10q
cat reports/mmr/E17_10q.md
```

Pour cibler les questions nécessitant plusieurs preuves :
```bash
python scripts/benchmark_mmr_e17.py --type multi_hop --limit 6 --output-prefix reports/mmr/E17_multihop_6q
```

Après contrôle du pilote, expérience complète :
```bash
python scripts/benchmark_mmr_e17.py --limit 100 --output-prefix reports/mmr/E17_100q
```

## Interprétation
Cinq bras : RRF5 vs MMR5 sans reranker ; RRF30+rerank, RRF15+rerank, MMR15+rerank. Même pool initial de 30 candidats, avec contrôle RRF15 pour isoler l'effet de la taille du pool. Le reranker peut être plus lent en CPU. Le jeu est le même pour tous les bras et n'active pas le filtre patient : les questions `cross_patient`, `cross_notice` et `multi_hop` exigent parfois plusieurs patients ou des notices générales. Une évaluation patient-filtrée viendra séparément, avec stratégie d'inclusion des notices.

L'évaluation reprend `judge_chunk`, `evaluate_fact_coverage` et `ndcg_at_k` existants, y compris la convention interne du nDCG « preuve unique » qui diffère d'un nDCG classique.

Les chiffres E11 historiques 88% / 92.63% / 80.89% sont des points de comparaison ; si la reproduction de `rrf30_rerank5` diffère, vérifier la version des index, les modèles, les données et la définition du score avant toute conclusion.

`mean_latency_seconds` est une durée par bras comprenant une partie commune des recherches, et ne mesure pas le coût complet indépendant de chaque architecture.
