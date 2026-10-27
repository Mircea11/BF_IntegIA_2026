# Cours personnel 01 — SQL : de la donnée brute à une base exploitable

**Parcours : AI Integration Specialist, Bruxelles Formation — consolidation au 26 octobre 2026**  
**Durée de lecture : 50–70 min | Pratique : 2 × 45 min**  
**Sources :** « 2026-04 - Cours SQL.md » (support de ton collègue), GitHub `Mircea11/BF_IntegIA_2026`, historique des exercices B5 et RAG.

> **But :** comprendre pourquoi tu as utilisé PostgreSQL dans B5 et dans le pipeline RAG, savoir lire un schéma et écrire toi-même des requêtes de base. Ce document ne constitue pas une certification de compétence.

## 1. Ta situation actuelle : ce qui est prouvé et ce qui reste à prouver

| Élément | Évidence observable | Niveau à retenir |
|---|---|---|
| Utiliser PostgreSQL dans un projet | B5 inclut une connexion PostgreSQL, une table de messages et des requêtes de lecture/écriture. | **Intégré dans un projet**, mais autonomie SQL non démontrée |
| Comprendre un schéma de données | `rag/demo/queries/schema.sql` définit `run` et `document`, avec une relation par clé étrangère. | **Vu / manipulé**, autonomie à tester |
| Comprendre le stockage persistant | Historique de conversation retrouvé après redémarrage n8n dans les tests antérieurs. | **Comportement testé**, installation et diagnostic indépendant à confirmer |
| Écrire SELECT/JOIN/GROUP BY sans IA | Aucun test indépendant suffisamment documenté dans les sources vérifiées pour ce premier cours. | **À évaluer** |

**Règle d'étude :** ne considère pas « j'ai exécuté un workflow » comme synonyme de « je saurais le reconstruire seul ».

## 2. Pourquoi SQL ? Relier ta carrière antérieure au nouveau métier

Dans la planification de production, les données arrivent de plusieurs systèmes : commandes, capacités, prévisions, stocks, réalisations. Sans règles de structure, deux analystes peuvent calculer des indicateurs contradictoires. Une base relationnelle sert à stocker des faits identifiables et à expliciter leurs relations. SQL permet de retrouver, croiser et agréger ces faits pour la décision.

**Ta chaîne métier cible :** sources → ingestion → contrôle qualité → stockage structuré → transformation → rapport/tableau de bord → décision. SQL se situe au cœur du **stockage et des transformations** ; un LLM ne remplace pas ces règles de qualité.

### Vocabulaire utile

- **Donnée** : valeur enregistrée, par exemple `stock = 0`.
- **Information** : donnée replacée dans un contexte, par exemple « Volleyball indisponible au moment de la vérification ».
- **Table** : ensemble d'enregistrements du même type (`document`, `run`, `message`).
- **Ligne** : occurrence, par exemple un document traité.
- **Colonne / attribut** : propriété, par exemple `status_`.
- **Clé primaire (PK)** : identifiant unique et non nul de chaque ligne.
- **Clé étrangère (FK)** : colonne faisant référence à une PK (ou clé unique) d'une autre table.
- **NULL** : valeur absente / inconnue, différente de `0` ou d'une chaîne vide. On teste `IS NULL`.

## 3. Modélisation : entités, cardinalités et relations

Le support de ton collègue commence par **entités, associations, cardinalités**, puis le passage aux tables. Garde cet ordre : on modélise d'abord, on écrit le SQL ensuite.

**Exemple réel :** le schéma GitHub du RAG contient deux tables :

```
run
  run_id (PK)
  start_time
  end_time
  doc_processed, doc_ignored, doc_failed
  parameters (JSONB)
       1
       │
       │ peut concerner 0 à N documents
       ▼
document
  document_id (PK)
  run_id (FK → run.run_id)
  file_path, file_name, file_format_
  file_hash, status_, process_time, error ...
```

**Interprétation :** un traitement (« run ») peut référencer plusieurs documents. Le document mémorise le numéro du traitement auquel il appartient. La FK se place dans `document`, c'est-à-dire du côté « plusieurs ». **Nuance importante :** le schéma actuel n'impose pas `document.run_id NOT NULL`, donc un document sans traitement associé reste possible dans la base ; ne pas annoncer une obligation que le DDL n'impose pas.

Pour une relation **N:N**, on crée une table de liaison. Exemple hypothétique `produit_fournisseur(produit_id, fournisseur_id)` avec PK composée des deux colonnes. Le support présente aussi les relations **1:1**, les héritages et les attributs multivalués : lis-les, mais applique d'abord solidement le cas 1:N du RAG.

### Clés et intégrité

Une **PK** empêche d'avoir deux lignes ayant le même identifiant. Une **FK** évite de référencer un parent inexistant, sous réserve que la contrainte soit effectivement appliquée. Une contrainte **UNIQUE** empêche les doublons sur une combinaison de colonnes. Un **NOT NULL** rend une valeur obligatoire.

## 4. Comprendre le vrai SQL de ton dépôt

**Fichier vérifié :** `RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql`.

Extrait fidèle, réduit aux champs structurants :

```sql
CREATE TABLE IF NOT EXISTS run (
    run_id SERIAL CONSTRAINT PK_RUN_ID PRIMARY KEY,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    parameters JSONB
);

CREATE TABLE IF NOT EXISTS document (
    document_id SERIAL CONSTRAINT PK_DOCUMENT_ID PRIMARY KEY,
    run_id INT CONSTRAINT FK_DOCUMENT_RUN REFERENCES run(run_id),
    file_name VARCHAR(255),
    status_ VARCHAR(255)
);
```

Les extraits ci-dessus sont **pédagogiquement abrégés** : pour l'exécution, utiliser le fichier complet dans GitHub.

- `CREATE TABLE IF NOT EXISTS` : ne crée la table que si elle n'existe pas ; ne vérifie pas si une table existante a le bon schéma.
- `SERIAL` : commodité historique PostgreSQL pour générer des entiers ; dans un nouveau schéma, `GENERATED ... AS IDENTITY` est souvent préférable.
- `TIMESTAMPTZ` : date/heure prenant en compte le fuseau lors de la conversion ; PostgreSQL la stocke sous forme d'instant absolu.
- `DEFAULT NOW()` : remplit automatiquement la date si elle n'est pas fournie.
- `JSONB` : données JSON stockées sous une forme optimisée pour les opérations PostgreSQL ; ce n'est pas une alternative générale à une bonne modélisation.
- `REFERENCES run(run_id)` : contrainte de FK.

### SQL Server ≠ PostgreSQL

Le support d'avril parle surtout de **SQL Server / T-SQL**, mais tes scripts récents utilisent **PostgreSQL**. Les principes relationnels sont communs, pas toutes les syntaxes.

| Concept | SQL Server, support collègue | PostgreSQL, tes projets |
|---|---|---|
| Identifiant auto-généré | `IDENTITY(1,1)` | `GENERATED BY DEFAULT AS IDENTITY` ou `SERIAL` existant |
| Paramètre de requête | souvent `@nom` | selon bibliothèque `$1`, `%s` ou paramètres nommés |
| Date/heure avec fuseau | `DATETIMEOFFSET` | `TIMESTAMPTZ` |
| JSON | traitements JSON selon version | type `JSONB` natif |
| Limiter le résultat | `TOP (10)` / `OFFSET FETCH` | `LIMIT 10` |

**À retenir :** apprends un dialecte opérationnel d'abord (**PostgreSQL**) ; reconnais ensuite les particularités du T-SQL.

## 5. Lire les données : SELECT, WHERE, ORDER BY

Les exemples suivants s'appuient sur les noms des tables du RAG. Ils sont à exécuter uniquement sur une base où ce schéma est présent.

```sql
-- Quels documents sont enregistrés ?
SELECT document_id, file_name, status_
FROM document
ORDER BY document_id DESC
LIMIT 10;
```

```sql
-- Quels documents n'ont pas de statut ?
SELECT document_id, file_name
FROM document
WHERE status_ IS NULL;
```

```sql
-- Quels traitements ont une date de début ?
SELECT run_id, start_time, end_time
FROM run
WHERE start_time IS NOT NULL
ORDER BY start_time DESC;
```

**Erreur fréquente :** `WHERE status_ = NULL` ne fonctionne pas comme attendu. En SQL, les comparaisons impliquant NULL sont généralement de valeur logique « inconnue ».

## 6. Croiser les tables : JOIN

```sql
SELECT
    d.document_id,
    d.file_name,
    d.status_,
    r.run_id,
    r.start_time
FROM document AS d
JOIN run AS r ON r.run_id = d.run_id
ORDER BY r.start_time DESC, d.document_id;
```

Lecture : « Pour chaque document qui correspond à un traitement, affiche ses informations et la date du traitement. »

- `INNER JOIN` (ou `JOIN`) : ne renvoie que les lignes ayant une correspondance.
- `LEFT JOIN` : conserve toutes les lignes à gauche, même sans correspondance à droite.

**Question-clé :** si tu veux inclure les `run` n'ayant traité aucun document, il faut partir de `run` et faire un `LEFT JOIN` vers `document`.

## 7. Agréger pour piloter : GROUP BY et COUNT

```sql
SELECT
    r.run_id,
    COUNT(d.document_id) AS documents_enregistres
FROM run AS r
LEFT JOIN document AS d ON d.run_id = r.run_id
GROUP BY r.run_id
ORDER BY r.run_id;
```

`COUNT(d.document_id)` donne **0** pour un traitement sans document. `COUNT(*)`, dans ce `LEFT JOIN`, compterait la ligne de résultat même quand les colonnes de `document` valent NULL. C'est une distinction importante pour les KPI.

**Attention au sens métier :** `COUNT(document_id)` compte les lignes enregistrées, pas nécessairement les documents *réussis*, *uniques* ou *traités correctement*. Définir le KPI avant de produire le tableau de bord.

## 8. Ce que PostgreSQL conserve dans B5

Tu as travaillé sur un assistant de recommandation B5 comprenant **n8n + PostgreSQL + Qdrant + modèle de langage**.

Rôles différents :

| Outil | Ce qu'il garde / fait | Ne fait pas |
|---|---|---|
| PostgreSQL | Historique structuré `session_id`, rôle, message, date | Recherche sémantique vectorielle par défaut |
| Qdrant | Vecteurs et métadonnées de produits pour similarité | Gestion naturelle des échanges conversationnels |
| BGE-M3 / vLLM | Transforme le texte en vecteur | Stockage fiable des conversations |
| Nemotron | Produit le texte de réponse à partir du contexte fourni | Garantie intrinsèque des prix ou du stock |
| n8n | Orchestration des appels, transformations et contrôles | Remplacement du stockage persistant |

**Observation documentée :** les tests précédents ont retrouvé un historique PostgreSQL après redémarrage de n8n. Cela prouve un comportement en situation de test, **pas** encore ta capacité à reconstruire seul les tables et les requêtes. Le projet comporte plusieurs variantes de workflow : ne pas confondre leur état de validation.

### Le lien avec une application réelle

Lorsqu'un client écrit « Je m'appelle Sam », une application peut conserver ce message dans une table conversationnelle. Lorsqu'il écrit « Comment je m'appelle ? », l'application doit retrouver le bon historique **pour la bonne session**, puis le fournir au modèle. Le stockage ne suffit pas : il faut des identifiants de session distincts pour éviter de mélanger plusieurs clients.

## 9. Apprendre sans dépendre de l'IA : travail personnel

### Bloc A — 45 min : compréhension et lecture

1. Sans ouvrir ChatGPT, dessine le schéma `run → document` et nomme PK, FK, sens du lien.
2. Explique à voix haute pourquoi `document.run_id` peut être NULL dans le fichier actuel.
3. Recopie les clauses `SELECT`, `FROM`, `WHERE`, `JOIN`, `GROUP BY`, `ORDER BY` dans leur ordre logique de lecture.
4. Écris trois requêtes sur papier : documents sans statut, derniers traitements, nombre de documents par traitement.

### Bloc B — 45 min : exécution guidée par les preuves

1. Sur le Z4, **localise la base PostgreSQL qui possède `run` et `document`**. Ne présume pas que c'est la même base que B5.
2. Ouvre le fichier `schema.sql` dans ton dépôt local ou GitHub et relie chaque colonne à un objectif métier.
3. Si les tables existent, exécute les trois requêtes ci-dessus ; sinon, travaille dans une base de test dédiée, sans toucher aux tables de production.
4. Conserve un fichier `sql_notes_01.md` avec tes requêtes, les résultats obtenus, la base utilisée et deux erreurs rencontrées.

### Autotest — réponds sans IA

1. Quelle est la différence entre une PK et une FK ?
2. Où place-t-on la FK dans une relation 1:N ?
3. Pourquoi `= NULL` est-il incorrect ?
4. Pourquoi `COUNT(d.document_id)` et `COUNT(*)` diffèrent-ils après un `LEFT JOIN` ?
5. Quel outil du B5 gère les vecteurs de produits ? Lequel conserve les messages ?
6. Quelle est la différence entre « un modèle a répondu Sam » et « la mémoire est persistante » ?
7. Que fait `CREATE TABLE IF NOT EXISTS` si une table existe avec des colonnes incorrectes ?
8. Une table `document` avec `run_id` nullable permet-elle un document sans traitement ?

**Critère de maîtrise indépendante :** produire seul un `SELECT` filtré, un `JOIN` et un `GROUP BY` corrects sur ton propre schéma et interpréter leurs résultats.

## 10. Petit pont vers ta future activité professionnelle

Cas concret : un service de données de chaîne d'approvisionnement. Les tables `produit`, `stock_observe`, `commande`, `fournisseur` doivent préciser leurs relations et la date d'observation. Sans horodatage, « stock disponible » peut devenir une information périmée. Le même principe explique le contrôle de stock en direct dans B5 : la similarité trouvée par Qdrant ne prouve pas la disponibilité commerciale.

**Preuve de travail possible pour ton showroom :** une courte page « Concevoir et interroger un schéma PostgreSQL pour tracer des documents ou des stocks », accompagnée d'un schéma, de trois requêtes et de résultats anonymisés. Ne la publier qu'après exécution autonome et vérification.

## 11. Références réelles, classées par provenance

**Support de ton collègue (source primaire du plan de cours)**
- `2026 Cours.zip` → `2026-04 - Cours SQL.md`, titre « Cours SQL — modélisation et SQL déclaratif ». Parties : modélisation, cardinalités, héritage, clés, `CREATE TABLE`, `ALTER TABLE`, jointures, agrégations, sous-requêtes, DML, transactions et T-SQL. Le présent cours **ne prétend pas couvrir intégralement** tous ces chapitres : il sélectionne les prérequis dont tu as besoin maintenant.

**Fichiers réellement vérifiés sur GitHub**
- [Schéma PostgreSQL du pipeline RAG — `schema.sql`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql) : tables `run` et `document`, FK et types PostgreSQL.
- [B5 — Guide de configuration sur le Z4](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md) : rôle de PostgreSQL, Qdrant, n8n, BGE-M3, Nemotron et tests de mémoire ; document de configuration, **pas une preuve que toutes les étapes ont été exécutées**.
- [B5 — installation et paramètres PostgreSQL](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/setup.sh) : variables d'environnement, volume persistant, vérification de connexion ; à lire, ne pas exécuter pendant une journée de révision.
- [B5 — application Python](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py) : exemple de lien entre application, base et services IA ; à explorer après les bases de SQL.

**Historique de notre travail (contexte de pratique, distinct de GitHub)**
- B5 : lectures/écritures PostgreSQL, tests de persistance, indexation Qdrant, vérification du stock et dépannage n8n. Ces opérations ont été réalisées au moins partiellement avec assistance. La validation indépendante reste à documenter.

**Ordinateur Z4**
- Chemin Git local connu : `/home/bm/formation`.
- Les services Docker et fichiers en fonctionnement **n'ont pas été inspectés directement sur le Z4** pour produire ce document. Les adresses d'API et configurations publiées dans GitHub sont des références de projet, pas une vérification de disponibilité actuelle.

---

**Prochain document prévu :** *Cours 02 — Python pour la data science (mai 2026)*, selon la chronologie du ZIP, après ta lecture ou tes réponses à l'autotest du cours 01. Si l'objectif est de consolider SQL d'abord, les documents PostgreSQL du mois de juillet seront traités ensuite dans la même série.
