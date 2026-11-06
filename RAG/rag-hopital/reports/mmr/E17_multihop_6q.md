# E17 — MMR vs RRF : benchmark lecture seule

Date (UTC) : 2026-11-05T14:46:30.806374+00:00
Questions : 6 ; candidats RRF : 30 ; pool MMR : 15 ; diversity : 0.6
Filtres patient : **désactivés pour toutes les stratégies**, conformément à la baseline E11.
Les questions multi-patients et celles qui requièrent des notices ne sont donc pas exclues.

## Moyennes (sur les questions exécutées)

| Stratégie | Hit@5 | Fact Recall@5 | nDCG@5 | Jaccard entre résultats | Durée/question* |
|---|---:|---:|---:|---:|---:|
| rrf5 | 33.3% | 58.3% | 44.4% | 0.0857 | 0.08 s |
| mmr5 | 16.7% | 41.7% | 34.3% | 0.0097 | 0.03 s |
| rrf30_rerank5 | 33.3% | 58.3% | 48.8% | 0.0776 | 15.24 s |
| rrf15_rerank5 | 33.3% | 58.3% | 50.5% | 0.0809 | 5.64 s |
| mmr15_rerank5 | 33.3% | 58.3% | 47.8% | 0.0066 | 7.18 s |

*Durée par stratégie non strictement indépendante : recherches initiales partagées pour certaines stratégies ; ne pas comparer comme coût total de production.*

## Méthodologie

- Même jeu de questions et mêmes preuves de référence pour toutes les stratégies.
- `rrf5` : cinq premiers de RRF ; `mmr5` : cinq premiers de MMR parmi les candidats RRF.
- `rrf30_rerank5` : reranker tous les candidats RRF ; correspond à la logique E11.
- `rrf15_rerank5` : reranker les premiers éléments RRF du même pool ; contrôle de taille.
- `mmr15_rerank5` : reranker un sous-ensemble diversifié par MMR.
- Hit@5 = tous les faits nécessaires présents ; nDCG à preuves uniques = convention E11 locale.
- Les nombres 30/15 sont des valeurs paramétrables ; ne pas généraliser un résultat d’un petit pilote.
- Requêtes Qdrant et fichiers source en lecture seule ; aucune écriture PostgreSQL.

## Résultats par type de question

| Type | Stratégie | N | Hit@5 | Fact Recall@5 | nDCG@5 |
|---|---|---:|---:|---:|---:|
| multi_hop | rrf5 | 6 | 33.3% | 58.3% | 44.4% |
| multi_hop | mmr5 | 6 | 16.7% | 41.7% | 34.3% |
| multi_hop | rrf30_rerank5 | 6 | 33.3% | 58.3% | 48.8% |
| multi_hop | rrf15_rerank5 | 6 | 33.3% | 58.3% | 50.5% |
| multi_hop | mmr15_rerank5 | 6 | 33.3% | 58.3% | 47.8% |

## Précautions

- La comparaison sur un petit échantillon ne démontre pas un gain généralisable.
- MMR est appliqué aux candidats RRF et utilise les vecteurs dense pour diversifier.
- Le filtre par patient doit faire l’objet d’une évaluation séparée : le filtre strict exclut les notices générales.
- En cas de divergence avec les scores historiques E11, vérifier les versions du corpus, des index et du reranker.
