# Cours personnel 04 — PostgreSQL procédural : comprendre et écrire du PL/pgSQL

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Source principale :** `2026-07-27_29 - SQL procédural PostgreSQL.md`, dans `2026 Cours.zip`, notes de Piu Ly (27–29 juillet 2026).  
**Rythme :** 55–75 min de lecture + 3 blocs pratiques de 45 min. Un bloc suffit pour une journée chargée.  
**Suite des cours :** 01 fondements SQL → 02 Python → 03 modélisation PostgreSQL → **04 logique procédurale dans PostgreSQL**.

> **Résultat attendu :** pouvoir expliquer et écrire sans assistance un bloc `DO`, déclarer une variable, contrôler son contenu, récupérer une valeur avec `SELECT ... INTO`, traiter l'absence de résultat et décider quand garder la logique dans SQL, Python ou n8n.

## 1. Ce que le cours contient réellement

Ton collègue distingue explicitement les notes prises pendant le cours et des ajouts ultérieurs pour couvrir le plan. Il est important de ne pas attribuer ces compléments à l'enseignement effectivement suivi.

| Élément | Statut dans le support | Priorité pour toi |
|---|---|---|
| `DO`, `DECLARE`, `BEGIN … END`, `:=` | **Notes de cours** | **A — À faire seul** |
| `RAISE NOTICE` pour tester par étapes | **Notes de cours** | **A — À faire seul** |
| `SELECT … INTO`, option `STRICT` | **Notes de cours** | **A — À faire seul** |
| `EXIT` / `CONTINUE` dans les boucles | **Notes de cours** | **A — À reconnaître et tester** |
| Types `%TYPE`, `%ROWTYPE`, `RECORD` | Complément ajouté | B — Comprendre |
| `IF` / `ELSIF` / `CASE`, boucles `FOR` / `WHILE` | Complément ajouté | A/B — Savoir lire, écrire un cas simple |
| Fonctions et procédures | Complément de syntaxe | B — Savoir expliquer, puis tester |
| Gestion d'exceptions | Complément ajouté | B — Savoir lire un exemple |
| Curseurs explicites et triggers | **Non vus en cours** | C — En réserve |

**Attention aux preuves de maîtrise :** le fait que le code apparaisse dans ton dépôt ou dans un notebook corrigé prouve la présence d'un artefact, pas que tu l'as conçu et exécuté sans aide.

## 2. Où se place le PL/pgSQL dans ton système réel ?

**Ton architecture actuelle, dans ses grandes lignes :** sources de documents et API → Python/Docling → PostgreSQL pour les métadonnées et journaux → embeddings BGE-M3 et recherche Qdrant → application Python/n8n et LLM Nemotron.

La différence fondamentale :

- **SQL déclaratif** : tu dis *quelles données* rechercher ou modifier (`SELECT`, `INSERT`, `UPDATE`).
- **PL/pgSQL procédural** : tu écris une séquence *d'étapes* dans PostgreSQL, avec variables, tests, boucles et exceptions.
- **Python** : tu coordonnes des fichiers, des APIs, des transformations et plusieurs services externes.
- **n8n** : tu orchestres les étapes du workflow et les appels à ces services.

Il ne faut pas écrire un trigger ou une fonction stockée simplement parce que PostgreSQL les permet. Pour B5, les appels à DummyJSON, Qdrant et Nemotron restent mieux placés dans le service applicatif ou n8n ; les requêtes de conservation de la mémoire sont naturellement placées dans PostgreSQL.

### Références vérifiées dans ton GitHub

| Projet | Fichier vérifié | Utilisation pertinente |
|---|---|---|
| RAG / ETL | [`schema.sql`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql) | Tables **`run`** et **`document`** pour les exécutions et les documents |
| RAG / ETL | [`exercice_01_pipeline_corrige.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb) | Pipeline Python utilisant `psycopg` et les tables **`runs`**, **`documents`** |
| B5 — Python | [`app.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py#L43-L87) | Tables **`b5_messages`**, **`b5_profile`** ; requêtes paramétrées depuis Python |
| B5 — tests | [`test_b5.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py) | Tests simulés, sans preuve de maîtrise PL/pgSQL |

**Trois schémas distincts :** `run/document`, `runs/documents` et `b5_messages/b5_profile` correspondent à des fichiers ou implémentations différents. Ne les mélange pas. Le workflow n8n V3.2 étudié précédemment utilise également une autre table, `public.b5_chat_messages` ; sa structure n'est pas celle de `app.py`.

**État de preuve :** SQL dans Python et modélisation visibles dans GitHub ; aucune fonction ou procédure PL/pgSQL créée et exécutée indépendamment n'a été identifiée dans les fichiers vérifiés. Cette compétence reste **à démontrer**, pas « acquise ».

## 3. Bloc `DO` : ton premier programme exécuté par PostgreSQL

Un bloc `DO` exécute une logique immédiatement sans enregistrer une fonction. C'est un bon terrain d'entraînement avant d'écrire du code persistant.

```sql
DO $$
DECLARE
    v_nom TEXT;
    v_age INTEGER := 51;
BEGIN
    v_nom := 'Charlotte';
    RAISE NOTICE 'Nom : %, âge : %', v_nom, v_age;
END;
$$;
```

**Lecture ligne par ligne :**

1. `DO` : exécuter ce bloc une seule fois.
2. `$$ … $$` : délimiter le corps du programme ; les guillemets simples à l'intérieur n'ont pas besoin d'être doublés.
3. `DECLARE` : réserver les variables `v_nom`, `v_age`.
4. `:=` : affecter une valeur (différent du `=` des comparaisons SQL).
5. `BEGIN … END` : délimiter les instructions.
6. `RAISE NOTICE` : afficher une information de diagnostic dans les messages du client SQL.

`RAISE NOTICE` ressemble à `print()` en Python, mais s'exécute **sur le serveur PostgreSQL**. Selon l'outil client, les notices apparaissent dans l'onglet « Messages », et non dans la grille des résultats `SELECT`.

**Méthode du cours :** vérifier *de façon jalonnée*. Déclarer → affecter → afficher → seulement ensuite ajouter une condition ou une requête.

## 4. `SELECT … INTO` : chercher une donnée dans une variable

Le support de cours utilise :

```sql
SELECT nom INTO v_nom FROM users WHERE id = 1;
SELECT nom INTO STRICT v_nom FROM users WHERE id = 1;
```

Ces exemples présupposent une table `users`. **Ne les lance pas tels quels sur ton Z4** : cette table n'est pas attestée dans les schémas vérifiés. Le mot `INTO` ici appartient au langage **PL/pgSQL**, dans un bloc `DO` ou une fonction ; il n'est pas équivalent à un `CREATE TABLE AS`.

| Nombre de lignes renvoyées | Sans `STRICT` | Avec `STRICT` |
|---|---|---|
| 0 | Variable `NULL`, pas d'erreur | Exception `NO_DATA_FOUND` |
| 1 | Valeur affectée | Valeur affectée |
| Plus de 1 | Une ligne retenue, sans garantie d'ordre si pas de `ORDER BY` | Exception `TOO_MANY_ROWS` |

Un exemple autonome sans table de travail :

```sql
DO $$
DECLARE
    v_message TEXT;
BEGIN
    SELECT 'pipeline RAG actif'
      INTO STRICT v_message;
    RAISE NOTICE 'Message : %', v_message;
END;
$$;
```

Ce cas doit réussir car `SELECT` renvoie une seule ligne. Il permet de voir la syntaxe, mais **ne prouve pas encore** que tu sais traiter une vraie table.

## 5. Conditions : exprimer une règle de qualité des données

Voici une **adaptation pédagogique**, non une règle extraite de ton code :

```sql
DO $$
DECLARE
    v_echecs INTEGER := 2;
BEGIN
    IF v_echecs = 0 THEN
        RAISE NOTICE 'Exécution sans erreur';
    ELSIF v_echecs <= 3 THEN
        RAISE NOTICE 'Exécution à revoir';
    ELSE
        RAISE NOTICE 'Exécution à investiguer';
    END IF;
END;
$$;
```

- `IF … THEN` : premier cas.
- `ELSIF … THEN` : cas supplémentaire.
- `ELSE` : tous les autres cas.
- `END IF` : fermeture de la condition.

En Python, tu écrirais `if/elif/else`. En n8n, tu utiliserais éventuellement un nœud IF ou Switch. Ici, le contrôle s'exécute au plus près des données.

**Précision importante :** en SQL, une comparaison qui renvoie `NULL` n'est pas `TRUE`. Pour vérifier une absence de valeur : `IS NULL`, et non `= NULL`.

## 6. Boucles : reconnaître `CONTINUE` et `EXIT`

Le cours mentionne `CONTINUE` et `EXIT`. Les formes suivantes apparaissent dans le complément de syntaxe.

```sql
DO $$
DECLARE
    v_i INTEGER;
BEGIN
    FOR v_i IN 1..6 LOOP
        CONTINUE WHEN v_i % 2 = 0;
        RAISE NOTICE 'Nombre impair : %', v_i;
        EXIT WHEN v_i >= 5;
    END LOOP;
END;
$$;
```

Résultat attendu : `1`, `3`, `5`.

**Ne pas confondre :** la plage PL/pgSQL `1..6` **inclut 6**, contrairement à `range(1, 6)` en Python, qui s'arrête à 5. Ici, `EXIT` arrête la boucle lorsque 5 est atteint ; `CONTINUE` saute les nombres pairs.

Dans de nombreuses opérations de données, un `UPDATE` ou `SELECT` portant sur un ensemble est préférable à une boucle ligne par ligne. **Ne transforme pas une requête SQL simple en boucle PL/pgSQL sans raison.**

## 7. Fonctions stockées et procédures : à quoi servent-elles ?

Le support contient ces notions dans les **compléments ajoutés après les notes**, et non dans la première partie attestée du cours.

Une **fonction** peut retourner une valeur et être appelée dans un `SELECT`. Voici un exemple d'apprentissage, indépendant de B5 :

```sql
-- Uniquement dans une base d'exercice autorisée.
CREATE OR REPLACE FUNCTION exercice_categorie_stock(p_stock INTEGER)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_stock IS NULL THEN
        RETURN 'inconnu';
    ELSIF p_stock <= 0 THEN
        RETURN 'indisponible';
    ELSE
        RETURN 'disponible';
    END IF;
END;
$$;

SELECT exercice_categorie_stock(0) AS resultat;
-- attendu : indisponible
```

Cela permettrait de ranger une règle strictement liée aux données en base. **Mais B5 vérifie les stocks depuis l'API DummyJSON :** cette fonction pédagogique ne remplacerait pas le contrôle de fraîcheur effectué dans Python ou n8n.

Une **procédure** s'appelle avec `CALL`. Elle peut notamment organiser une opération interne à la base. À retenir : ses opérations de contrôle transactionnel (`COMMIT`, `ROLLBACK`) ne sont possibles que dans les contextes autorisés, notamment lorsque `CALL` n'est pas exécuté à l'intérieur d'un bloc de transaction explicite. **Évite l'exemple `UPDATE produits SET prix = ...` du support sur toute table réelle : il modifierait tous les prix.**

| Question | Fonction | Procédure |
|---|---|---|
| Appel normal | `SELECT fonction(...)` | `CALL procedure(...)` |
| Valeur retournée | Avec `RETURNS ...` | Pas de valeur de retour par `RETURN` comme dans une fonction ; paramètres `OUT` possibles |
| Usage fréquent | Calcul / validation / recherche | Traitement administratif sur les données |
| Transactions internes | Pas de `COMMIT`/`ROLLBACK` dans une fonction | Possible dans des contextes précis |

## 8. Gestion des erreurs : repérer un résultat inattendu

Le complément introduit `EXCEPTION`. L'exemple suivant peut être **lu et exécuté sans modifier la base** :

```sql
DO $$
DECLARE
    v_resultat TEXT;
BEGIN
    BEGIN
        SELECT x
          INTO STRICT v_resultat
          FROM (SELECT 'A'::TEXT AS x WHERE FALSE) AS t;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE NOTICE 'Aucune ligne trouvée : cas contrôlé';
        WHEN TOO_MANY_ROWS THEN
            RAISE NOTICE 'Plusieurs lignes : cas contrôlé';
    END;
END;
$$;
```

Ici, le sous-ensemble `WHERE FALSE` ne renvoie aucune ligne : avec `STRICT`, PostgreSQL lève `NO_DATA_FOUND`, puis la branche `EXCEPTION` l'intercepte. **Ce n'est pas une preuve que ton B5 emploie actuellement cette construction** ; c'est un exercice pour comprendre ce comportement.

## 9. Curseurs et triggers : savoir les situer, sans disperser le travail

Le support indique que **les curseurs explicites et les triggers n'ont pas été vus pendant le cours**.

- **Curseur** : permet de parcourir le résultat d'une requête ligne par ligne. La boucle `FOR rec IN SELECT ...` utilise déjà un mécanisme de parcours implicite. Un curseur explicite demande d'ouvrir, récupérer puis fermer.
- **Trigger** : exécute automatiquement une fonction lorsque des lignes sont insérées, modifiées ou supprimées. Exemple de cas professionnel : horodatage ou journal d'audit. Un trigger peut créer des effets de bord difficiles à voir ; il faut le documenter et le tester.

À ce stade, **ne crée pas de trigger sur les tables B5 ou RAG**. Le gain de compétences à court terme est inférieur au risque d'introduire une erreur dans une base fonctionnelle.

## 10. Trois blocs pratiques de 45 minutes

### Bloc A — Maîtriser la mécanique, sans toucher aux tables (45 min)

**Sans IA pendant la première tentative.** Dans un éditeur SQL relié à PostgreSQL :

1. Écris un bloc `DO` qui déclare `v_source TEXT := 'RAG'` et `v_nombre INTEGER := 4`.
2. Affiche ces deux valeurs dans une unique ligne `RAISE NOTICE`.
3. Ajoute un `IF` : si `v_nombre = 0` affiche « aucun », sinon « éléments présents ».
4. Remplace `4` par `0` et vérifie la seconde branche.
5. Sans exécuter, explique chaque ligne à voix haute ou par écrit.

**Critère :** retrouver la syntaxe correcte sans recopier l'exemple.

### Bloc B — `SELECT INTO STRICT` et diagnostic (45 min)

Sans modifier de table réelle :

1. Recopie le bloc autonome de la section 4, puis modifie le texte recherché.
2. Exécute le bloc avec `WHERE FALSE` de la section 8.
3. Supprime provisoirement `STRICT` et déduis la nouvelle valeur de `v_resultat`.
4. Remets `STRICT`, puis transforme la sous-requête en source de deux lignes, pour provoquer `TOO_MANY_ROWS`.
5. Note les trois états : 0, 1 et 2 lignes.

**Critère :** expliquer pourquoi `STRICT` aide à éviter un défaut silencieux dans le traitement de données.

### Bloc C — Rattacher la théorie à tes artefacts (45 min)

Ouvre les **trois références GitHub vérifiées** (schéma RAG, notebook corrigé, `app.py`) et réponds, sans inventer :

1. Où Python se connecte-t-il à PostgreSQL dans B5 ?
2. Quelle fonction Python crée les tables `b5_messages` et `b5_profile` ?
3. Quelle requête retrouve les messages d'une session ? Quel est son ordre de tri ?
4. Le code stocke-t-il la logique de mémoire dans une fonction PL/pgSQL ? **Réponse attendue : non, dans le code vérifié.**
5. Dans `schema.sql`, quelle clé relie `document` à `run` ?
6. Quelle vérification SQL pourrait signaler une exécution `run` ayant `end_time IS NULL` ? Écris un simple `SELECT`, pas une procédure.

**Critère :** distinguer SQL exécuté par un client Python et PL/pgSQL exécuté dans PostgreSQL.

## 11. Autotest de fin de cours (sans regarder les réponses)

1. À quoi sert `DO` ? La logique est-elle enregistrée pour un usage futur ?
2. Quelle différence entre `:=` et `=` dans un bloc PL/pgSQL ?
3. Où retrouver le résultat de `RAISE NOTICE` ?
4. Que signifie `SELECT ... INTO STRICT` si la requête renvoie 0, 1, ou 3 lignes ?
5. Quelle instruction saute une itération ? Laquelle sort de la boucle ?
6. Quelle est la différence entre `FOR i IN 1..5` et `range(1, 5)` ?
7. Quelle différence entre fonction et procédure dans PostgreSQL ?
8. Donne une raison de laisser l'appel Qdrant dans Python/n8n plutôt que dans un trigger SQL.
9. Où est enregistrée la mémoire B5 dans la version Python de ton dépôt ?
10. Une fonction PL/pgSQL exécutée sur ton Z4 est-elle déjà prouvée par le dépôt examiné ?

### Corrigé à consulter après l'essai

1. Exécuter un bloc anonyme une fois ; non enregistré comme fonction.  
2. `:=` affecte ; `=` compare des valeurs, par exemple dans `IF`.  
3. Messages/notices du client SQL (pas nécessairement grille de résultats).  
4. 0 → `NO_DATA_FOUND` ; 1 → valeur ; 3 → `TOO_MANY_ROWS`.  
5. `CONTINUE` et `EXIT`.  
6. En PL/pgSQL, 5 est inclus ; en Python, 5 est exclu.  
7. Fonction : valeur de retour, usage typique dans `SELECT` ; procédure : `CALL`, traitement, contrôle transactionnel sous conditions.  
8. L'appel Qdrant est une opération externe d'orchestration ; les triggers doivent rester centrés sur la cohérence en base.  
9. `b5_messages` et `b5_profile`, avec la logique de `remember()`, `recent()`, `name_get()` et `name_put()` dans `app.py`.  
10. Non : des usages SQL sont visibles, pas une preuve d'exécution autonome de fonctions PL/pgSQL.

## 12. Positionnement des compétences et suite

| Niveau | Indice concret | État au 26/10/2026 |
|---|---|---|
| Vu / reconnu | Lecture du support et reconnaissance des mots clés | **Documenté** |
| Avec assistance | Travail préalable sur SQL, Python/`psycopg`, ETL et B5 | **Documenté** |
| Indépendant | Écrire seul un `DO` avec variable, `SELECT INTO STRICT`, erreur et condition | **À vérifier** |
| Prouvé sur un cas réel | Script testé et expliqué, intégrant un contrôle utile à un ETL | **Non démontré** |

**Ne lance pas un nouveau chantier technique pour ce cours.** L'actif public reste ton portfolio GitHub, le travail technique principal reste l'intégration de données / IA, et PL/pgSQL sert ici de fondation. Un exercice autonome réussi suffit pour clore ce module.

**Prochain support dans la chronologie du ZIP :** `2026-08-03_10 - Bases Python et visualisation.md` (cours 05). Il sera articulé avec le cours 02 pour éviter de répéter les mêmes notions sans ajouter de preuves de maîtrise.

---

**Traçabilité des sources.** Les notions et leur statut « notes de cours » ou « complément » proviennent du fichier de ton collègue `2026-07-27_29 - SQL procédural PostgreSQL.md`. Les tables et noms de fonctions cités pour B5 / RAG ont été vérifiés dans les fichiers GitHub liés ci-dessus. Les exercices, explications professionnelles et recommandations d'apprentissage sont des adaptations pédagogiques, et ne constituent pas des résultats d'exécution sur ton Z4.
