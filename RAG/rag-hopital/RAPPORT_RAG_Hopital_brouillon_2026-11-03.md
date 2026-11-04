# Hospital RAG — Rapport d'expériences (brouillon)

**Date de travail :** 3 novembre 2026  
**Projet :** `~/formation/RAG/rag-hopital`  
**Référence pédagogique :** `references/RagRecapCorrige`, branche `corrige`, commit `eb4df33`  
**État :** brouillon à compléter après l'évaluation des 100 questions avec reranking.

## 1. Objectif et méthode

Industrialiser une chaîne de recherche augmentée par récupération (RAG) sur les documents synthétiques du Centre Hospitalier de Valmont, mesurer ses performances, puis comparer des configurations en ne modifiant qu'une variable à la fois.

**Jeu d'évaluation :** 106 questions au total, dont 100 avec preuves documentaires pour l'évaluation déterministe et 6 questions `out_of_corpus` pour évaluer les refus de génération. Les six questions hors corpus ne sont pas actuellement prises en charge par le script d'évaluation déterministe local.

**Configuration utilisée pour les expériences 6 et 7 :** Docling HybridChunker, 512 tokens, ligne patient activée, overlap 0 ; embedder BGE-M3 ; fusion de recherche Dense + BM25 par RRF ; 30 candidats par branche ; 5 résultats finaux. L'expérience 7 ajoute BGE-reranker-v2-m3 exécuté sur CPU. La collection hybride comptait 1 173 points lors du dernier contrôle communiqué.

**Attention méthodologique :** les scores de nDCG de ce projet utilisent une convention de dédoublonnage des preuves. Ils ne doivent pas être comparés sans harmonisation aux scores produits par `ranx` dans le corrigé.

## 2. Expériences vérifiées

| Expérience | Configuration | Questions évaluées | Full-answer Hit@5 | Fact Recall@5 | nDCG@5 | État |
|---|---|---:|---:|---:|---:|---|
| 6 | Hybrid, sans reranker | 100 | 0,7700 | 0,8377 | 0,6955 | Résultats rapportés et enregistrés dans PostgreSQL |
| 7 | Hybrid + reranker CPU | 3 | 1,0000 | 1,0000 | 0,9532 | Terminé et évalué |
| À confirmer | Hybrid + reranker CPU | 100 visées | — | — | — | Exécution en cours au dernier point de suivi ; résultats non encore reçus |

*Ne pas comparer la ligne sur 100 questions à la ligne sur 3 questions comme s'il s'agissait du même échantillon.*

## 3. Comparaison appariée Q001–Q003 : expériences 6 et 7

| Question | Type | nDCG@5 sans reranker | nDCG@5 avec reranker | Évolution |
|---|---|---:|---:|---:|
| Q001 | `table` | 1,0000 | 0,8597 | −0,1403 |
| Q002 | `cross_patient` | 1,0000 | 1,0000 | 0,0000 |
| Q003 | `imaging` | 0,6309 | 1,0000 | +0,3691 |
| **Moyenne** |  | **0,8770** | **0,9532** | **+0,0763** |

Pour ces trois questions, le Full-answer Hit@5 et le Fact Recall@5 sont égaux à 1,0000 dans les deux expériences. Le reranker ne récupère donc aucun fait supplémentaire sur ce petit échantillon ; il modifie leur ordre. Son effet est négatif sur Q001, neutre sur Q002, positif sur Q003. L'échantillon est trop petit pour une conclusion générale.

**Latences de l'expérience 7 :** Q001 21,881 s, Q002 3,702 s, Q003 22,108 s. Durée totale enregistrée : 47,77 s. Ces temps incluent les coûts et variations d'exécution locale ; comparer les latences sur 100 questions avant de choisir une architecture.

## 4. Résultats complets — à renseigner après exécution

**ID de l'expérience :** À confirmer dans PostgreSQL.  
**Nombre de questions enregistrées :** À confirmer (attendu : 100).  
**Statut de l'expérience :** À confirmer (`done`).  
**Durée totale :** À confirmer.  
**Score moyen Full-answer Hit@5 :** À confirmer.  
**Score moyen Fact Recall@5 :** À confirmer.  
**Score moyen nDCG@5 :** À confirmer.

Comparer **les mêmes 100 identifiants de questions** aux scores de l'expérience 6. Ajouter ensuite la moyenne et les écarts par type de question, ainsi que les questions dont le classement s'améliore ou se dégrade.

## 5. Écarts constatés face à l'énoncé du formateur

- **Infrastructure / modules :** conversion, découpage, indexation, recherche Dense/Sparse/Hybrid, reranking et enregistrement PostgreSQL disponibles ; `README.md` du projet encore vide au dernier examen GitHub.
- **Variantes de chunking :** tailles et overlaps paramétrables, avec une collection Qdrant par index, restent à implémenter et comparer.
- **Paramètres :** tester le nombre de candidats (10/30/50), Top K (3/5/10), RRF vs DBSF et la latence ; le script actuel limite la plupart des choix.
- **Prompts et génération :** le pipeline actuel enregistre des passages, pas encore des réponses LLM ; tester quatre prompts et les six refus hors corpus après intégration.
- **Embedders / rerankers alternatifs :** comparaison avec un autre embedder et reranker non démontrée.
- **Filtres :** extraction d'identité et filtrage Qdrant, repli sans filtre et mesure des erreurs restent à réaliser.
- **Juge LLM :** évaluation d'un échantillon de 26 questions (2 par type répondable) non réalisée.
- **Deux optimisations supplémentaires :** à sélectionner et mesurer parmi les pistes de la section 8.
- **Interface :** le formateur dispose de pages Streamlit pour logs, comparaison d'expériences et performances LLM ; leur code a été examiné, mais l'interface n'a pas été lancée ou vérifiée visuellement dans notre environnement.

## 6. Limites et précautions

- La configuration du corrigé du formateur n'est pas identique à notre environnement local ni à notre schéma SQL ; ne pas exécuter ses scripts directement contre notre base.
- Le corrigé vérifié contient un paramètre TOML `candidates = 30a` dans `experiments/baseline.toml`, qui n'est pas syntaxiquement valide ; il faut vérifier le corrigé avant réutilisation.
- Les résultats de récupération ne mesurent ni la fidélité de la réponse générée ni les refus sur les questions hors corpus.
- Les temps du reranker CPU peuvent être élevés et variables. Ne pas conclure à partir de trois questions.

## 7. Prochaines actions dans l'ordre

1. Confirmer le statut `done`, le nouvel ID d'expérience et les 100 résultats sauvegardés.
2. Calculer les six métriques déterministes via `--evaluate-existing ID`.
3. Comparer à l'expérience 6 à questions appariées, globalement et par catégorie ; retenir trois cas d'échec et analyser leurs passages.
4. Intégrer la génération LLM en conservant la séparation entre récupération, génération et évaluation.
5. Réaliser les optimisations de l'énoncé et compléter le classement expérimental.
6. Finaliser `README.md`, `RAPPORT.md` et une interface de consultation sans écriture dans les bases.

**Document de travail :** aucun score de l'expérience complète avec reranking n'a été inventé ou anticipé.
