# RAG Hôpital — Rapport expérimental

## 1. Objectif

Construire et évaluer un système RAG local sur un corpus
hospitalier fictif, de l'indexation documentaire à la génération
de réponses sourcées.

## 2. Architecture

- Extraction et découpage des documents en chunks.
- Taille cible : 512 tokens, avec identification du patient.
- Embeddings : BGE-M3.
- Recherche hybride : dense + BM25, fusion RRF.
- Base vectorielle : Qdrant.
- Reranking : BGE-reranker-v2-m3.
- Génération : Qwen 3.5 9B via vLLM.
- Persistance des expériences : PostgreSQL.
- Évaluation indépendante : Granite 4.1 8B.

## 3. Évaluation du retrieval — E11

Échantillon : 100 questions répondables.

| Métrique | Sans reranking (ID 6) | Avec reranking (ID 8) |
|---|---:|---:|
| Hit@5 | 77,0 % | 88,0 % |
| Fact Recall@5 | 83,77 % | 92,63 % |
| nDCG@5 | 69,55 % | 80,89 % |

Le reranking améliore les trois métriques mesurées.

## 4. Génération — E12

Expérience PostgreSQL : ID 12.

- Questions : 106/106.
- Questions répondables : 100.
- Questions hors corpus : 6.
- Temps moyen de génération : 15,93 secondes.
- Prompt de référence : 10 règles.

### Gestion des questions hors corpus

- Refus corrects : 5/6 (83,3 %).
- Échec : Q045, réponse non justifiée sur la metformine.
- Trois refus explicites injustifiés : Q063, Q078, Q089.

Le comptage des refus exacts ne couvre pas toutes les réponses
exprimant une impossibilité de répondre autrement.

## 5. Évaluation LLM-as-Judge — E14

Échantillon reproductible : 26 questions, deux pour chacune
des 13 catégories répondables.

- Générateur évalué : Qwen 3.5 9B.
- Juge : Granite 4.1 8B.
- Exactitude moyenne : 92,3 %.
- Complétude moyenne : 80,8 %.
- Réponses jugées exactes : 24/26.
- Réponses jugées complètes : 18/26.
- Réponses incorrectes : Q011 et Q089.

Ces notes mesurent la correspondance avec les réponses
de référence. Elles ne prouvent pas la fidélité documentaire.

## 6. Analyse de trois erreurs

### Q045 — Inférence injustifiée

Le système déduit que Mme Michèle Bernard ne prend pas
de metformine parce que les passages retrouvés mentionnent
d'autres médicaments.

Diagnostic : erreur de génération. L'absence de mention
ne permet pas de conclure à l'absence de traitement.

Correction : ajout d'une règle 11 interdisant cette inférence.

### Q063 — Mauvais chunk

Le document d'échocardiographie du bon patient est retrouvé,
mais le système sélectionne son en-tête.

L'information attendue, « insuffisance mitrale modérée »,
figure dans le chunk 2 du même document, présent dans Qdrant.

Diagnostic : sélection insuffisante des passages.

### Q089 — Preuves incomplètes

Le système refuse de répondre concernant l'association
ramipril et sacubitril/valsartan.

La référence indique une contre-indication et un délai
de 36 heures entre les traitements.

Le détecteur de preuves retrouve 1 fait sur 2 dans le top 5.

Diagnostic : récupération documentaire partielle,
à confirmer par inspection complète des passages.

## 7. Amélioration V2

Une règle 11 a été ajoutée au prompt opérationnel pour
interdire les conclusions injustifiées sur l'absence
d'un médicament ou de sa posologie.

La configuration V2 est préparée.
Son effet n'a pas encore été évalué expérimentalement.

Les résultats chiffrés présentés restent ceux du baseline E12.

## 8. Limites

- Évaluation LLM-as-Judge sur 26 questions seulement.
- Les 6 questions hors corpus sont évaluées séparément.
- Les citations numériques ne garantissent pas la fidélité.
- Certaines erreurs demandent une inspection des chunks.
- Le jugement automatique peut contenir des erreurs.
- Les variations de classement E11/E12 concernent 2 questions
  sur les 100 questions communes.

## 9. Conclusion

Le système RAG fonctionne de bout en bout et conserve ses
résultats expérimentaux dans PostgreSQL.

Le reranking améliore la recherche documentaire.
Les principaux axes d'amélioration sont la sélection
des passages, les réponses multi-documents et la prévention
des inférences non justifiées.

Tous les documents médicaux utilisés sont fictifs.
Ce projet est pédagogique et ne constitue pas un outil
d'aide à la décision clinique.

## 10. Résultats conservés

- `reports/E12_baseline_106_answers.csv`
- `reports/E12_judge_sample_26.json`
- `reports/E12_judge_26_granite8b.jsonl`
- `reports/E12_judge_summary.md`
- `prompts/baseline_detailed_v1.txt`
- `prompts/hopital_strict_v1.txt`
