# Cours personnel 03 — PostgreSQL : modéliser, interroger et tracer les données

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Support du collègue :** `2026-07-13_27 - Modélisation et SQL déclaratif PostgreSQL.md` (13–27 juillet 2026).  
**Temps conseillé :** 60–80 min de lecture, puis trois blocs de 45 min, fractionnables.  
**Position dans le parcours :** approfondissement PostgreSQL après le cours 01 (SQL général) et le cours 02 (Python).

> **Objectif mesurable :** savoir expliquer le schéma d'un pipeline ETL, lire les requêtes réellement présentes dans tes projets, écrire seul les requêtes de contrôle d'exécution et comprendre ce que PostgreSQL conserve pour B5. Aucun niveau de maîtrise indépendante n'est présumé.

## 1. Ce cours apporte quoi de plus que le cours 01 ?

Le cours 01 expliquait une table, les relations et les requêtes simples. Celui-ci introduit les **choix qui rendent une base fiable** : contraintes, transactions, dialecte PostgreSQL, suivi des exécutions, fenêtres, vues et requêtes reproductibles. Ce sont les notions qui relient tes compétences historiques de contrôle des données à la pratique actuelle de l'IA.

**Architecture à garder en tête** : document ou API → Python/Docling → PostgreSQL (journal, données structurées) → embeddings / Qdrant (recherche sémantique) → application / n8n (décision et réponse). PostgreSQL ne remplace pas Qdrant ; chacun répond à un besoin différent.

**Preuves disponibles :** ton dépôt contient un `schema.sql` (`run`, `document`), un notebook de pipeline ETL corrigé (`runs`, `documents`) et une application B5 (`b5_messages`, `b5_profile`). **Attention : ces trois schémas ne sont pas identiques.** Ne jamais copier une requête de l'un dans l'autre sans vérifier les noms réels des tables et colonnes.

## 2. Passer d'un besoin métier à un modèle relationnel

Le support distingue l'entité, les attributs, la cardinalité, les associations et la nullabilité. Reprends un cas concret : chaque *exécution* de ton ETL traite zéro, un ou plusieurs documents ; chaque *document traité* appartient à une exécution.

| Concept du cours | Ton pipeline RAG | Conséquence SQL |
|---|---|---|
| Entité | Exécution `run` | Une ligne par tentative de traitement |
| Entité | Document `document` | Une ligne par document traité |
| Relation 1–N | `run` → `document` | `document.run_id` est une clé étrangère |
| Clé primaire | `run.run_id` | Identifier une exécution de manière unique |
| Attribut optionnel | `end_time`, `error` | Peut être `NULL` |
| Traçabilité | `status_`, `process_time`, compteurs | Analyser réussite, échec et durée |

Dans **le schéma GitHub**, la table `run` contient `run_id`, `start_time`, `end_time`, `doc_processed`, `doc_ignored`, `doc_failed`, `parameters JSONB`. La table `document` contient entre autres `document_id`, `run_id`, `file_path`, `file_name`, `file_hash`, `status_`, `process_time` et `error`.

**À ne pas confondre :** le notebook *corrigé* définit des tables au pluriel `runs` et `documents`, avec des colonnes comme `processed_count`, `failure_count` et `sha256`. Les exercices plus loin mentionnent explicitement à quel schéma ils se rapportent.

## 3. Le langage SQL : cinq fonctions différentes

| Famille | Exemple | À quoi cela te sert |
|---|---|---|
| DDL | `CREATE TABLE`, `ALTER TABLE` | Définir le schéma et ses contraintes |
| DML | `INSERT`, `UPDATE`, `DELETE` | Alimenter ou corriger les enregistrements |
| DQL / DRL | `SELECT` | Mesurer, comparer et diagnostiquer |
| TCL | `BEGIN`, `COMMIT`, `ROLLBACK` | Garantir une opération cohérente |
| DCL | `GRANT`, `REVOKE` | Contrôler les autorisations |

**Les quatre propriétés ACID :** atomicité = tout ou rien ; cohérence = contraintes respectées ; isolation = transactions concurrentes séparées selon le niveau choisi ; durabilité = modifications validées conservées après panne. Une transaction utile en ETL peut enregistrer le traitement et ses métriques ensemble, plutôt que laisser un journal partiel.

```sql
BEGIN;
UPDATE run
SET end_time = NOW(), doc_processed = 3
WHERE run_id = 7;
-- Vérifier avant validation
ROLLBACK;  -- annule l'essai ; remplacer par COMMIT seulement si voulu
```

Cet exemple est **didactique** : ne l'exécute pas sur les données réelles de formation sans sélectionner une base de test. En lecture seule, commence par `SELECT`.

## 4. Les contraintes : transformer des hypothèses en règles

```sql
-- Modèle pédagogique : à exécuter dans une base de test uniquement
CREATE TABLE exercice_run (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_count INTEGER NOT NULL DEFAULT 0
        CHECK (processed_count >= 0)
);

CREATE TABLE exercice_document (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES exercice_run(id),
    file_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success','failed','skipped'))
);
```

`PRIMARY KEY` identifie une ligne ; `FOREIGN KEY` protège la relation ; `NOT NULL` exige une valeur ; `CHECK` impose une condition métier ; `UNIQUE` empêche certains doublons. Le support note qu'en PostgreSQL, une contrainte `UNIQUE` accepte plusieurs `NULL` par défaut ; `UNIQUE NULLS NOT DISTINCT` permet de changer ce comportement.

Dans un service de données, la robustesse provient d'abord de telles règles explicites, puis des contrôles programmatiques. L'existence d'un `run_id` ne suffit pas à garantir que l'ETL s'est terminé.

## 5. Lire réellement les données du schéma `run` / `document`

**Exemple 1 — dernières exécutions**

```sql
SELECT run_id, start_time, end_time,
       doc_processed, doc_ignored, doc_failed
FROM run
ORDER BY start_time DESC
LIMIT 10;
```

**Exemple 2 — documents échoués**

```sql
SELECT document_id, run_id, file_name, error
FROM document
WHERE status_ = 'failed'
ORDER BY document_id DESC;
```

**Exemple 3 — résultat d'une exécution et documents associés**

```sql
SELECT r.run_id, r.start_time,
       d.file_name, d.status_, d.process_time
FROM run AS r
LEFT JOIN document AS d ON d.run_id = r.run_id
ORDER BY r.run_id DESC, d.document_id;
```

Pourquoi `LEFT JOIN` ? Pour conserver une exécution même quand aucun document associé n'a été enregistré. C'est essentiel pour détecter les essais vides ou interrompus.

**Exemple 4 — mesure de fiabilité**

```sql
SELECT r.run_id,
       COUNT(d.document_id) AS documents_journalises,
       COUNT(*) FILTER (WHERE d.status_ = 'failed') AS echecs,
       ROUND(AVG(d.process_time)::numeric, 2) AS duree_moyenne
FROM run AS r
LEFT JOIN document AS d ON d.run_id = r.run_id
GROUP BY r.run_id
ORDER BY r.run_id DESC;
```

**Piège important :** `COUNT(*)` sur un `LEFT JOIN` compterait une ligne pour une exécution sans document. On utilise `COUNT(d.document_id)` pour compter les documents existants. Le filtre `status_ = 'failed'` correspond à une convention possible ; vérifie d'abord les valeurs réelles avec `SELECT DISTINCT status_ FROM document`.

## 6. Les particularités de PostgreSQL à reconnaître

| Construction | Signification | Exemple |
|---|---|---|
| `'texte'` | Valeur textuelle | `WHERE status_ = 'failed'` |
| `"NomColonne"` | Identifiant cité, sensible à la casse | `SELECT "MaColonne"` |
| `::` | Conversion de type | `AVG(process_time)::numeric` |
| `ILIKE` | Motif sans sensibilité à la casse | `file_name ILIKE '%.pdf'` |
| `IS NULL` | Absence de valeur | `WHERE end_time IS NULL` |
| `DATE_TRUNC` | Regroupement temporel | `DATE_TRUNC('day', start_time)` |
| `JSONB` | Document JSON indexable/interrogeable | `parameters` dans `run` |

Deux pièges classiques : `= NULL` ne trouve pas les valeurs manquantes ; pour des prix/montants exacts, préfère `NUMERIC` aux flottants quand la précision décimale est contractuelle.

Le support du collègue signale aussi des mélanges de dialectes SQL Server/MySQL : `CURDATE()`, `DATEDIFF()`, `AS 'Mon alias'`, `OUTPUT` ne doivent pas être recopiés sans adaptation. En PostgreSQL, on utilise par exemple `CURRENT_DATE`, les opérateurs de dates, `AS "Mon alias"` et `RETURNING`.

## 7. CTE, vues et fenêtres : produire des indicateurs d'exploitation

**CTE : rendre le calcul lisible.** Une *Common Table Expression* commence par `WITH` et nomme un résultat intermédiaire.

```sql
WITH activite AS (
  SELECT DATE_TRUNC('day', start_time)::date AS jour,
         SUM(COALESCE(doc_processed, 0)) AS documents
  FROM run
  GROUP BY 1
)
SELECT jour, documents,
       LAG(documents) OVER (ORDER BY jour) AS veille,
       SUM(documents) OVER (ORDER BY jour
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumul
FROM activite
ORDER BY jour;
```

- `GROUP BY` regroupe les exécutions par jour.
- `LAG` retrouve la valeur de la ligne précédente : ici **le jour observé précédent**, pas nécessairement le jour civil précédent s'il manque des dates.
- `SUM() OVER (...)` calcule un cumul sans supprimer les lignes.
- `COALESCE(x, 0)` remplace une valeur absente par zéro pour le calcul.

**Vue vs vue matérialisée :** une vue classique enregistre une requête ; une vue matérialisée stocke un résultat qui doit être rafraîchi (`REFRESH MATERIALIZED VIEW`). Pour un tableau de bord, la première privilégie l'actualité des données ; la seconde peut réduire le coût de calcul, au risque d'afficher des données anciennes.

## 8. La mémoire PostgreSQL du projet B5 : deux structures à distinguer

Le dépôt GitHub contient une version Python de B5 dans `N8N/B5_conseiller_produit_v2/app.py`. Elle déclare :

- `b5_messages` : messages de chaque session (conversation et rôle) ;
- `b5_profile` : prénom associé à un `session_id` ;
- des fonctions `remember`, `recent`, `name_get`, `name_put`.

**Point crucial :** le workflow n8n V3.2 travaillé dans la conversation utilisait une autre table, `public.b5_chat_messages`, et l'identifiant de démonstration fixe `b5-demo-001`. Ne mélange pas les deux implémentations. La liste de tables réellement présentes doit être vérifiée sur la base et le conteneur appropriés.

```sql
-- Uniquement dans la base qui contient la table Python B5
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'b5_%'
ORDER BY table_name;
```

À comprendre : le modèle de langage n'est pas une base de données persistante. La mémoire après redémarrage dépend de l'écriture des messages/profils et de leur relecture avec le bon identifiant de session. Ce mécanisme explique un intérêt professionnel réel : séparer données structurées, recherche sémantique et génération de réponses.

## 9. Travail autonome — 3 blocs de 45 minutes

### Bloc A — Lecture et reconstruction (45 min, sans IA)

1. Ouvre `schema.sql` sur GitHub. Dessine deux rectangles `run` / `document` avec leurs clés et une flèche.
2. Explique pourquoi la relation est 1–N ; identifie trois champs possiblement `NULL`.
3. Sans copier le cours, écris une requête donnant les dix dernières exécutions et une requête recensant les échecs.
4. Compare ensuite avec les exemples du §5 ; note les écarts.

**Preuve à conserver :** schéma dessiné + deux requêtes personnelles.

### Bloc B — Requêtes de contrôle (45 min, base de test)

1. Ouvre la bonne base PostgreSQL ; confirme les noms de tables (`\dt` dans `psql` ou requête `information_schema`).
2. Exécute `SELECT DISTINCT status_ FROM document;` puis adapte le filtre d'échec.
3. Écris un `LEFT JOIN` et un `GROUP BY` pour compter les documents par exécution.
4. Explique pourquoi `COUNT(d.document_id)` est préférable à `COUNT(*)` dans cet exemple.

**Preuve :** fichier `.sql` avec tes requêtes et sorties non sensibles.

### Bloc C — De la mesure au tableau de bord (45 min)

1. Calcule les documents traités par jour, puis une moyenne par exécution avec `AVG`.
2. Ajoute `LAG` et une somme cumulée ; décris les différences entre `GROUP BY` et `OVER`.
3. Rédige un mini-indicateur destiné à un responsable de production : volume, échecs, durée, retard d'exécution.
4. Identifie ce qui manquerait pour auditer le processus (horodatages, données manquantes, version du modèle, source).

**Preuve :** un tableau de 4 indicateurs avec leur formule SQL et limite d'interprétation.

## 10. Autotest et positionnement des compétences

Réponds sans regarder le document :

1. Qu'est-ce qui distingue une clé primaire d'une clé étrangère ?
2. Pourquoi les documents doivent-ils référencer l'exécution ETL ?
3. Quelle différence entre `NULL`, `0` et chaîne vide ?
4. Que deviennent les modifications après `ROLLBACK` ?
5. Pourquoi utiliser `LEFT JOIN` pour détecter une exécution sans document ?
6. Quelle différence entre `GROUP BY` et `ROW_NUMBER() OVER (...)` ?
7. Quelles tables PostgreSQL B5 existent dans la version Python ; pourquoi ne peut-on pas les supposer identiques à la version n8n ?
8. Quelle information manque si l'on connaît seulement le nombre de documents traités ?

**Échelle de preuve :** `Vu` = notion rencontrée ; `Assisté` = réalisée avec support ; `Autonome` = réussie sans aide et expliquée ; `Prouvé` = reproductible sur tes propres données avec résultat conservé. Aucune note de compétence « autonome » n'est attribuée ici sans exercice corrigé.

## 11. Liens vérifiables vers ton travail

**Support primaire, non publié :** `2026 Cours.zip` → `2026-07-13_27 - Modélisation et SQL déclaratif PostgreSQL.md` ; complément de juillet SQL procédural reporté au cours suivant.

**GitHub — projet réel (état consulté le 26 octobre 2026) :**

- Schéma RAG `run` / `document` : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql
- Notebook corrigé ETL : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb
- Application Python B5 (`b5_messages`, `b5_profile`) : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py
- Guide d'installation B5 : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md

**Historique de travail discuté ensemble :** workflow n8n B5 V3.2, connexion PostgreSQL, mémoire après redémarrage et GitHub (commit distant `c17017e`). Ce contexte prouve le travail réalisé et les étapes franchies, **pas encore l'autonomie SQL**.

**Suite cohérente :** cours 04 — SQL procédural PostgreSQL (PL/pgSQL) : fonctions, variables, conditions, boucles, exceptions et frontières entre SQL et Python.
