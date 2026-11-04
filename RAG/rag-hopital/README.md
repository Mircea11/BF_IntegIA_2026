
<!-- RAG-HOPITAL-E12-E14 -->
## Résultats du projet — E11 à E14

### Architecture
- Extraction et découpage : 512 tokens
- Embeddings : BGE-M3
- Recherche hybride : dense + BM25, fusion RRF
- Base vectorielle : Qdrant
- Reranking : BGE-reranker-v2-m3
- Génération : Qwen 3.5 9B via vLLM
- Persistance : PostgreSQL
- LLM-as-Judge : Granite 4.1 8B

### Résultats

| Indicateur | Résultat |
|---|---:|
| Hit@5 avec reranking | 88 % |
| Fact Recall@5 | 92,63 % |
| nDCG@5 | 80,89 % |
| Questions générées | 106/106 |
| Refus hors corpus corrects | 5/6 |
| Exactitude LLM-as-Judge | 92,3 % |
| Complétude LLM-as-Judge | 80,8 % |

Les résultats de génération concernent le baseline E12.
L'évaluation LLM-as-Judge porte sur 26 questions.

### Documentation et résultats
- `RAPPORT.md` : rapport expérimental
- `experiments/` : configurations
- `prompts/` : baseline et prompt V2
- `reports/E12_baseline_106_answers.csv` : 106 réponses
- `reports/E12_judge_26_granite8b.jsonl` : évaluations
- `reports/E12_judge_summary.md` : synthèse
- `scripts/run_experiment.py` : exécution
- `scripts/judge_e12.py` : juge automatique

### Configuration

Vérification sans lancer de nouvelle expérience :

    PYTHONPATH=src python scripts/run_experiment.py experiments/hybrid_bge_bm25_rerank_qwen9b.toml --check-config

### État
- Baseline E12 : expérience PostgreSQL ID 12.
- Prompt V2 : règle 11 intégrée.
- Amélioration V2 : non encore mesurée.
- Usage : projet pédagogique sur données médicales fictives.

