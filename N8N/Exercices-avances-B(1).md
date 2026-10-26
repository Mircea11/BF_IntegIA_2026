# Exercices avancés — Série B — Formation n8n

Cinq business cases plus complexes que la série A : chacun demande un **workflow complet**, parfois
**plusieurs workflows** qui collaborent. Aucun node n'est imposé : à vous d'analyser le besoin, de
choisir les nodes, de les enchaîner et de vérifier le résultat. Plusieurs besoins nécessitent des
nodes **pas encore vus en cours** : la documentation n8n et la recherche dans le panneau d'ajout de
nodes font partie de l'exercice.

**Difficulté.** 🟡 moyen · 🔴 difficile — les exercices sont classés par difficulté croissante.

---

## Boîte à outils

**API ouvertes, sans clé**

| Service | Contenu |
|---|---|
| `https://dummyjson.com` | Clients, produits, avis factices d'une boutique en ligne |
| `https://date.nager.at` | Jours fériés officiels par pays et par année |

**Base de données.** La base PostgreSQL de la formation est accessible depuis n8n avec l'hôte
`postgres`, le port `5432` ; les identifiants sont fournis par le formateur. Les tables des exercices
sont créées dans le schéma `formation` :

```sql
CREATE SCHEMA IF NOT EXISTS formation;
```

**Prérequis IA (B.4 et B.5)**
- Un modèle de langage et un modèle d'embeddings : credential fournie par le formateur (OpenAI), ou
  modèles locaux via Ollama.
- La base vectorielle **Qdrant**, démarrée avec `docker compose -f docker-compose-BETA.yml up -d`.
  Depuis n8n : adresse `http://qdrant:6333`, clé `QDRANT_API_KEY` du fichier `.env`. Tableau de bord :
  `http://localhost:6333/dashboard`.

---

## B.1 — La synchronisation du CRM 🟡

**Le besoin**
> Une agence commerciale utilise un outil SaaS dans lequel ses clients sont saisis. Elle souhaite en
> disposer d'une copie dans sa propre base de données, **mise à jour chaque nuit à 2h**. L'API de
> l'outil renvoie les clients **par pages de 50 au maximum** : le workflow doit parcourir toutes les
> pages, quel que soit le nombre de clients. Un client déjà présent en base est mis à jour, un nouveau
> client est ajouté : la table ne doit jamais contenir de doublon. Chaque synchronisation laisse une
> trace dans un journal : date, nombre de clients lus, nombre de nouveaux, nombre de clients déjà
> connus.

**Ressources**
- Clients, page par page : `https://dummyjson.com/users?limit=50&skip=0` (`skip` = nombre de clients à
  sauter ; la réponse indique `total`, `skip` et `limit`).
- Champs à conserver : identifiant, prénom + nom (un seul champ), email, téléphone, ville
  (`address.city`), entreprise (`company.name`), rôle.
- Tables à créer :
  ```sql
  CREATE TABLE IF NOT EXISTS formation.clients (
    id           INTEGER PRIMARY KEY,
    nom_complet  TEXT NOT NULL,
    email        TEXT NOT NULL,
    telephone    TEXT,
    ville        TEXT,
    entreprise   TEXT,
    role         TEXT,
    synchro_le   TIMESTAMPTZ NOT NULL
  );

  CREATE TABLE IF NOT EXISTS formation.journal_synchro (
    id            SERIAL PRIMARY KEY,
    execute_le    TIMESTAMPTZ NOT NULL DEFAULT now(),
    nb_lus        INTEGER NOT NULL,
    nb_nouveaux   INTEGER NOT NULL,
    nb_existants  INTEGER NOT NULL
  );
  ```

**Résultat attendu**
- ✓ Le workflow se déclenche automatiquement chaque nuit à 2h.
- ✓ Le service est interrogé page par page (jamais plus de 50 clients par appel) et le parcours
  s'arrête de lui-même après la dernière page.
- ✓ Après une première exécution, `formation.clients` contient autant de lignes que le `total` annoncé
  par l'API, et le journal indique autant de nouveaux que de clients lus.
- ✓ Une seconde exécution ne crée aucun doublon ; le journal indique 0 nouveau.
- ✓ Après suppression manuelle de 3 clients et modification de l'email d'un 4ᵉ en base, la synchro
  suivante recrée les 3 clients (3 nouveaux au journal) et rétablit l'email d'origine.

**Objectif** : parcourir une API paginée, synchroniser une base sans doublon et tracer chaque exécution.

---

## B.2 — L'API catalogue pour les partenaires 🔴

**Le besoin**
> Un grossiste veut offrir à ses revendeurs partenaires une **adresse de consultation** de son
> catalogue, sans leur donner accès à ses systèmes. Un partenaire interroge l'adresse en précisant une
> catégorie, et éventuellement un prix maximum, un ordre de tri et un numéro de page. Il reçoit une
> réponse JSON simple : pour chaque produit, son identifiant, son nom, son **prix TVAC (21 %)**, sa
> note et sa disponibilité (oui / non) ; et des informations de pagination (page courante, nombre de
> pages, nombre total de résultats). Les résultats sont servis par **pages de 5**.
>
> Les erreurs doivent être explicites : paramètre manquant ou invalide → code **400** avec un message
> précisant le paramètre fautif ; catégorie inexistante → code **404**. La logique de recherche
> (filtrer, trier, paginer, calculer les prix) sera réutilisée prochainement par d'autres
> automatisations du grossiste : elle doit pouvoir être appelée **indépendamment** de l'adresse web.

**Ressources**
- Paramètres de l'adresse : `categorie` (obligatoire), `prix_max` (nombre, facultatif), `tri`
  (`prix_asc`, `prix_desc` ou `note_desc` — facultatif, `prix_asc` par défaut), `page` (entier ≥ 1,
  facultatif, 1 par défaut).
- Catégories existantes : `https://dummyjson.com/products/category-list`
- Produits d'une catégorie : `https://dummyjson.com/products/category/smartphones`
  (les prix du fournisseur sont hors TVA).
- Tests depuis un terminal (sous Windows PowerShell : `curl.exe`) :
  ```bash
  curl "<adresse>?categorie=smartphones&prix_max=500&tri=note_desc&page=2"
  curl "<adresse>?categorie=smartphones&tri=au_hasard"
  curl "<adresse>?categorie=bijoux"
  curl "<adresse>?prix_max=100"
  ```

**Résultat attendu**
- ✓ La première requête de test renvoie un code **200**, 5 produits, et indique 13 résultats répartis
  sur 3 pages.
- ✓ Les prix renvoyés sont TVAC, arrondis à 2 décimales ; un produit dont le stock est nul est
  indiqué comme indisponible.
- ✓ Le tri invalide et la catégorie manquante renvoient un code **400** avec un message nommant le
  paramètre en cause ; la catégorie inconnue renvoie un code **404**.
- ✓ La logique de recherche est un workflow distinct, testable seul avec des données d'exemple, et
  appelé par le workflow exposé.
- ✓ Le service fonctionne en mode production (workflow publié, adresse définitive).

**Objectif** : exposer un service web en lecture, valider des paramètres d'entrée et isoler une logique réutilisable.

---

## B.3 — La demande de congés 🔴

**Le besoin**
> Une PME belge souhaite dématérialiser ses demandes de congés. Un collaborateur remplit un
> **formulaire web** : son email (choisi dans une liste), une date de début, une date de fin et un
> motif facultatif. La demande est ensuite traitée ainsi :
> 1. Le nombre de jours décomptés est calculé : seuls les **jours ouvrables** comptent (ni samedi, ni
>    dimanche, ni **jour férié légal belge**).
> 2. La demande est **refusée automatiquement** si la date de fin précède la date de début, si la
>    date de début est passée, si la période ne contient aucun jour ouvrable, ou si le solde du
>    collaborateur est insuffisant. Le motif du refus est enregistré.
> 3. Sinon, un message est préparé pour le manager du collaborateur : il contient un **lien** vers une
>    page où le manager approuve ou refuse, avec un commentaire facultatif. Le traitement **attend** sa
>    réponse.
> 4. Si le manager approuve, le solde est diminué ; dans tous les cas, la décision est historisée.
> 5. Sans réponse du manager **sous 48 heures**, un message d'escalade est préparé pour le service RH
>    et la demande est historisée « en attente RH ».

**Ressources**
- Jours fériés : `https://date.nager.at/api/v3/PublicHolidays/2026/BE` (seuls les jours dont le type
  est `Public` sont des jours fériés légaux).
- Tables et données de départ :
  ```sql
  CREATE TABLE IF NOT EXISTS formation.conges_soldes (
    email         TEXT PRIMARY KEY,
    nom           TEXT NOT NULL,
    email_manager TEXT NOT NULL,
    solde_jours   INTEGER NOT NULL
  );

  INSERT INTO formation.conges_soldes VALUES
    ('alice.martin@exemple.be',  'Alice Martin',  'marc.dubois@exemple.be', 12),
    ('bruno.lambert@exemple.be', 'Bruno Lambert', 'marc.dubois@exemple.be', 3),
    ('chloe.peeters@exemple.be', 'Chloé Peeters', 'sarah.janssens@exemple.be', 20)
  ON CONFLICT (email) DO NOTHING;

  CREATE TABLE IF NOT EXISTS formation.conges_demandes (
    id           SERIAL PRIMARY KEY,
    email        TEXT NOT NULL REFERENCES formation.conges_soldes(email),
    date_debut   DATE NOT NULL,
    date_fin     DATE NOT NULL,
    nb_jours     INTEGER NOT NULL,
    statut       TEXT NOT NULL,   -- approuvee, refusee_manager, refusee_auto, en_attente_rh
    commentaire  TEXT,
    traitee_le   TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  ```
- Pour les tests, le délai de 48 heures peut être temporairement ramené à 2 minutes.

**Résultat attendu**
- ✓ Une demande d'Alice du lundi 9 au lundi 16 novembre 2026 compte **5 jours** (le 11 novembre est
  férié) ; après approbation du manager, son solde passe de 12 à 7 et la demande est historisée
  `approuvee`.
- ✓ Une demande de Bruno du 9 au 13 novembre 2026 (4 jours, solde 3) est refusée automatiquement,
  sans solliciter le manager, avec le motif « solde insuffisant ».
- ✓ Une demande couvrant uniquement un week-end, et une demande dont la fin précède le début, sont
  refusées automatiquement avec un motif explicite.
- ✓ Un refus du manager est historisé `refusee_manager` avec son commentaire ; le solde est inchangé.
- ✓ Sans réponse dans le délai, la demande est historisée `en_attente_rh` et un message d'escalade est
  produit.

**Objectif** : intégrer une validation humaine dans un processus automatisé, manipuler des dates et appliquer des règles métier.

---

## B.4 — L'analyse des avis clients 🔴

**Le besoin**
> Le responsable qualité d'une boutique en ligne lit chaque mois les avis laissés sur les produits
> d'une catégorie. Il souhaite automatiser ce travail. Pour chaque avis, il veut connaître :
> - le **sentiment** du texte : positif, neutre ou négatif ;
> - le **thème** principal : qualité, prix, livraison, conformité à la description, ou général.
>
> Les avis notés **3 étoiles** mais dont le texte est **négatif** l'intéressent particulièrement : ce
> sont des clients mécontents qui n'osent pas mettre une mauvaise note. Il veut un **rapport par
> produit** : nombre d'avis, nombre d'avis positifs et négatifs, thème le plus cité dans les avis
> négatifs, et la liste de ces avis « mécontents discrets ». L'analyse doit fonctionner pour n'importe
> quelle catégorie, et le modèle d'IA doit être sollicité par **paquets de 5 avis**, avec une courte
> pause entre deux paquets.

**Ressources**
- Produits et avis d'une catégorie : `https://dummyjson.com/products/category/sunglasses?select=title,reviews`
  (champ `reviews` : `rating`, `comment`, `reviewerName`).
- Le modèle de langage fourni par le formateur (voir *Prérequis IA*).

**Résultat attendu**
- ✓ Chaque avis est enrichi d'un sentiment et d'un thème, choisis **uniquement** parmi les valeurs
  listées ci-dessus (aucune autre valeur, aucun texte libre).
- ✓ Le modèle n'est jamais sollicité pour plus de 5 avis à la fois.
- ✓ Pour la catégorie `sunglasses`, le rapport contient 5 produits et 15 avis au total, et signale
  4 avis « mécontents discrets ».
- ✓ Le rapport est produit dans un fichier `/data/rapport_avis_<categorie>.csv` (une ligne par
  produit), et changer de catégorie ne demande qu'une modification à un seul endroit.

**Objectif** : utiliser un modèle d'IA comme étape de traitement de données, en obtenant une réponse structurée et fiable.

---

## B.5 — Défi : le conseiller produit 🔴

**Le besoin**
> Une boutique en ligne souhaite un **assistant conversationnel** qui conseille ses clients.
> L'assistant :
> - ne recommande **que** des produits du catalogue de la boutique, et répond qu'il ne sait pas
>   lorsqu'une question sort de ce catalogue ;
> - trouve les produits pertinents même si le client ne connaît pas leur nom exact (« un cadeau pour un
>   joueur de tennis », « de quoi cuisiner des pâtes ») ;
> - **vérifie le stock en temps réel** avant de recommander un produit, et propose une alternative
>   quand un produit est en rupture ;
> - se souvient de la conversation, **même après un redémarrage de n8n** ;
> - répond en français, avec le nom et le prix de chaque produit recommandé.
>
> Le catalogue évolue : un workflow séparé permet de le **réindexer** à la demande. Une réindexation ne
> doit jamais créer de doublon dans la base de connaissances de l'assistant.

**Ressources**
- Catalogue complet : `https://dummyjson.com/products?limit=0&select=title,description,category,price,brand`
- Stock d'un produit en temps réel : `https://dummyjson.com/products/132?select=title,stock,availabilityStatus`
- Base vectorielle Qdrant et modèles d'IA : voir *Prérequis IA*.
- Base PostgreSQL de la formation pour l'historique des conversations.

**Résultat attendu**
- ✓ Après indexation, la base vectorielle contient une entrée par produit du catalogue (194) ; une
  deuxième indexation laisse ce nombre inchangé.
- ✓ « Je cherche un smartphone Samsung à moins de 500 € » : l'assistant ne recommande pas le Samsung
  Galaxy S8 (en rupture) comme disponible et propose une alternative en stock.
- ✓ « Je voudrais un ballon de volley » : l'assistant signale la rupture du Volleyball et propose un
  autre produit de la catégorie sport.
- ✓ « Quel est le meilleur restaurant de Bruxelles ? » : l'assistant indique qu'il ne peut répondre
  qu'à propos du catalogue.
- ✓ Après « Je m'appelle Sam » puis un redémarrage du conteneur n8n, la question « Comment je
  m'appelle ? » dans la même conversation obtient la bonne réponse.
- ✓ Chaque produit recommandé existe réellement dans le catalogue, avec son prix exact.

**Objectif** : assembler un assistant IA complet — base de connaissances, outils, mémoire persistante — et en maîtriser les limites.
