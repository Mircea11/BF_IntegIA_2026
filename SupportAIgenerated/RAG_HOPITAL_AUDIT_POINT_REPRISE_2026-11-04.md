# RAG Hôpital — Audit et point de reprise

**État au 4 novembre 2026** — Le projet a été interrompu volontairement pour passer à un autre module de formation. Aucune reprise automatique n'est prévue. Ce document permet de le reprendre sans répéter les expériences.

## 1. Arrêt des services

Dernier journal fourni :

```text
(APIServer pid=25204) INFO: Shutting down
(APIServer pid=25204) INFO: Waiting for application shutdown.
(APIServer pid=25204) INFO: Application shutdown complete.
...resource_tracker.py:279: UserWarning: ... 1 leaked semaphore objects to clean up at shutdown
```

- **Constaté :** le processus API vLLM s'est arrêté, et le terminal est revenu à `~`.
- **Interprétation :** l'avertissement de sémaphore est associé à la fermeture de Python multiprocessing ; ce journal **ne démontre pas** une corruption du corpus, de PostgreSQL ou de Qdrant. Il ne permet pas non plus de confirmer l'état de ces autres services.
- **Conséquence :** au retour, vérifier les services et redémarrer ceux nécessaires aux nouveaux tests. Ne pas relancer les 106 questions de E12.

## 2. Travaux accomplis et contrôlés

| Bloc | Résultat | Statut |
|---|---|---|
| Infrastructure RAG | PostgreSQL, Qdrant, services vLLM BGE-M3 et Qwen3.5-9B ont fonctionné pendant les expériences ; reranker BGE-reranker-v2-m3 en CPU | **Fonctionnement passé démontré** ; état actuel à vérifier |
| Ingestion/indexation | Corpus fictif : environ 280 documents patient ; collection hybride `hopital_bge_m3_512_hybrid`, environ 1 173 chunks ; séparation 512 tokens avec préfixe patient ; cache BM25 | **Réalisé** ; paramètres exacts à vérifier dans les fichiers locaux |
| E11 — recherche | Expérience PostgreSQL ID 8 sur 100 questions, recherche hybride + reranking : Hit@5 0,88 ; Fact Recall@5 0,9263 ; nDCG@5 0,8089 | **Mesuré** |
| E12 — génération | Expérience PostgreSQL ID 12, statut `done`, **106/106 réponses** enregistrées (100 répondables + 6 hors corpus) ; cinq passages/réponse ; moyenne 15,93 s | **Vérifié par SQL et export** |
| Baseline prompt | Prompt original à dix instructions dans `prompts/baseline_detailed_v1.txt`, référencé par `experiments/hybrid_bge_bm25_rerank_qwen9b.toml` | **Validé lors de la campagne**, ne pas modifier |
| Variante future | Règle 11 ajoutée dans `references/RagRecapCorrige/prompts/detailed.txt` (copie locale de référence du formateur) | **Préparée mais non testée comme E13** |
| E11/E12 stabilité | Sur 100 questions : 98 classements de chunks identiques ; Q011/Q021 avec passages/ordre modifiés ; Q023/Q029 avec seules métadonnées différentes | **Vérifié par SQL** |
| Audit E12 | Export des 106 réponses, tableau Excel, rapport de clôture et couverture documentaire | **Produit** |

## 3. Mesures E12 — distinguer confirmé et provisoire

| Mesure | Résultat | Limite |
|---|---:|---|
| Refus *exacts* sur l'ensemble | 8 | Correspondance normalisée à « Je ne dispose pas de cette information » |
| Refus exacts corrects, hors corpus | 5/6 = 83,3 % | Q045 est la question hors corpus non refusée |
| Refus exacts injustifiés parmi les 100 répondables | 3/100 = 3 % | Q063, Q078, Q089 seulement pour la formulation stricte |
| Autres refus en langage libre | 5 | Q011, Q012, Q013, Q071, Q072 ; audit sémantique à confirmer |
| Refus injustifiés au sens large (lecture des réponses) | 8/100 = 8 % | Score provisoire |
| Réponses avec citation `[n]` | 96/106 | Présence syntaxique, **pas** validité du contenu cité |
| Couverture documentaire de tous les faits (100 répondables) | 91/100 | Calcul par **nom de document** dans le top 5, pas par contenu de chunk |
| Groupes de faits avec document de référence dans top 5 | 132/142 = 93,0 % | Ne mesure pas la présence du passage qui prouve le fait |
| Réponses conformes à la question principale | 86/106 = 81,1 % | **Évaluation provisoire**, non certifiée contre les textes complets de Qdrant |
| Autres classifications | 4 partielles ; 14 non conformes ; 2 à vérifier | Audit manuel comparatif provisoire |

**Ne pas appeler 81,1 % un score certifié de fidélité ni reprendre les métriques E11 comme métriques E12.**

### Diagnostics directement étayés

- **Q045 (génération)** : le modèle affirme que Mme Michèle Bernard ne prend pas de metformine. Il s'agit d'une inférence non justifiée par l'absence de prescription. Règle 11 = variante future à tester.
- **Q063 (recherche/ranking)** : dans le document d'imagerie du patient Claude Nicolas, le chunk **2** contient « Insuffisance mitrale modérée » ; E12 a passé le chunk **0**, contenant essentiellement l'en-tête. L'extraction/indexation est correcte ; le passage pertinent n'a pas été sélectionné.
- **Q078** : l'audit automatisé a reconnu **0/2** groupes de faits nécessaires parmi les passages E12 ; le détail des chunks reste à vérifier avant d'attribuer entièrement la faute à la recherche.
- **Q089** : l'audit automatisé a reconnu **1/2** groupes de faits ; analyse précise des passages encore requise.
- **Questions sans couverture documentaire complète** au sens des documents de référence : Q012, Q037, Q050, Q064, Q071, Q072, Q078, Q089, Q092.
- **Q017/Q083 et Q066/Q093** : cas supplémentaires à revoir sur texte intégral avant un verdict définitif.

## 4. Travail restant, par priorité

### P0 — Conservation et reprise sûre (à faire au retour, avant les tests)

1. Ne modifier ni **E12 ID 12** ni les résultats enregistrés. Aucun besoin de refaire le baseline.
2. Vérifier dans `~/formation/RAG/rag-hopital` que les fichiers de configuration, les prompts et les rapports sont toujours disponibles. Les rapports dans cette conversation sont des artefacts téléchargeables : **leur présence dans le dépôt local n'est pas confirmée**.
3. Exécuter `git status --short` à la racine appropriée (`~/formation`), vérifier les changements non committés et créer, après revue, un commit ciblé du code et de la configuration E12. **Le commit des derniers changements n'est pas confirmé.**
4. Vérifier l'état de Qdrant/PostgreSQL et des ports `8101` (embeddings) et `8102` (Qwen). Redémarrer uniquement les services nécessaires.

### P1 — Évaluation encore incomplète

5. Audit de fidélité **passage par passage** des cas litigieux : texte intégral des chunks Qdrant, preuves exactes, citations `[n]`, et classement retrieval / génération / benchmark ambigu.
6. Calculer **les métriques retrieval propres à E12**, puisque deux classements diffèrent de E11, et vérifier les définitions des métriques du professeur.
7. Réaliser l'évaluation par juge LLM sur l'échantillon fixe prévu par l'exercice (**26 questions, deux par type**, si l'énoncé local le confirme) ; enregistrer méthode, modèle et limites.

### P2 — Expériences futures, uniquement après reprise du projet

8. **E13 prompt** : dupliquer le TOML E12 sous un **nouveau nom et une nouvelle expérience** ; pointer vers un fichier de prompt contenant les dix règles + la règle 11 ; comparer Q045, les autres questions hors corpus et les régressions parmi les 100 répondables. **Une variable à la fois.**
9. **E14 retrieval** (séparé) : étudier le ranking multi-chunks, Q063, la fusion hybride, les questions multi-documents / notices et le top-k. Ne pas mélanger changement de prompt et changement de recherche dans la même expérience.
10. Finaliser le dépôt pédagogique : `README.md`, `RAPPORT.md`, limites, résultats comparatifs et au moins trois analyses d'échec selon la consigne du formateur.

### P3 — Développement ultérieur, non prioritaire maintenant

11. Reprise d'expériences interrompues, robustesse du runner (`try/finally`, statut d'échec, reprise par question), homogénéisation du cache BM25 pour l'indexation et la recherche, contrôle fin des paramètres de génération tels que `temperature`.

## 5. Point de reprise (copier dans le prochain échange)

> Reprendre `~/formation/RAG/rag-hopital` après pause. E11 retrieval ID 8 est terminé ; E12 baseline génération ID 12 est **done**, 106 réponses stockées ; les rapports de clôture sont disponibles dans la conversation. Le processus API vLLM a été arrêté volontairement ; avertissement de sémaphore à la sortie. Ne relancer aucune expérience existante. D'abord vérifier les services et `git status`, puis choisir **soit la fin de l'audit de fidélité**, **soit un nouvel E13 (règle 11 uniquement)**. La priorité immédiate de formation est un **autre module**, pas E13.

## 6. Fichiers existants dans la conversation

- `E12_baseline_106_answers.csv`
- `E12_baseline_rapport.md`
- `E12_baseline_audit.xlsx`
- `E12_baseline_audit_cloture.xlsx`
- `E12_couverture_documentaire_106.csv`
- `E12_CLOTURE_ET_REPRISE_2026-11-04.md`

**Règle de reprise :** distinguer *réalisé*, *mesuré*, *supposé* et *restant*. La réussite pédagogique de la campagne E12 ne signifie pas que l'ensemble des livrables du professeur est terminé.
