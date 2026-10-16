# Exercices avancés — Formation n8n

Six business cases demandant un **workflow complet** (une dizaine de nodes). Comme pour les exercices
du chapitre 1, aucun node n'est imposé : à vous d'analyser le besoin, de choisir les nodes, de les
enchaîner et de vérifier le résultat. Certains besoins nécessitent des nodes **pas encore vus en
cours** : la documentation n8n et la recherche dans le panneau d'ajout de nodes font partie de
l'exercice.

**Difficulté.** 🟡 moyen · 🔴 difficile — les exercices sont classés par difficulté croissante.

---

## Boîte à outils

**API ouvertes, sans clé**

| Service | Contenu |
|---|---|
| `https://dummyjson.com` | Paniers, produits, utilisateurs factices d'une boutique en ligne |
| `https://jsonplaceholder.typicode.com` | Utilisateurs, tâches, articles factices |
| `https://api.open-meteo.com` | Prévisions météo |
| `https://api.frankfurter.app` | Taux de change officiels (BCE), mis à jour les jours ouvrables |

**Fichiers.** Le dossier `data/` du projet est visible dans n8n sous le chemin `/data/`.
Les fichiers produits par vos workflows doivent être écrits dans `/data/`.

**Base de données.** La base PostgreSQL de la formation est accessible depuis n8n avec
l'hôte `postgres`, le port `5432` ; les identifiants sont fournis par le formateur.
Les tables des exercices sont créées dans un schéma dédié `formation` :

```sql
CREATE SCHEMA IF NOT EXISTS formation;
```

---

## A.1 — Le rapport des ventes 🟡

**Le besoin**
> Un e-commerçant souhaite un rapport de ventes établi à partir de l'ensemble de ses paniers. Il veut
> connaître le chiffre d'affaires total (montants après remises), le nombre de paniers, le panier
> moyen, ainsi que le **top 5 des produits les plus vendus** en quantité, avec pour chacun la
> quantité vendue et le chiffre d'affaires généré. Les montants de la boutique sont en dollars
> américains ; le rapport doit être exprimé en **euros, au taux du jour**.

**Ressources**
- Paniers : `https://dummyjson.com/carts?limit=0`
- Taux de change : `https://api.frankfurter.app/latest?from=USD&to=EUR`

**Résultat attendu**
- ✓ Un fichier `/data/top5_produits.csv` contenant 5 lignes : produit, quantité vendue, CA en EUR.
- ✓ Un texte de synthèse prêt à envoyer reprenant CA total, nombre de paniers et panier moyen en EUR
  (montants arrondis à 2 décimales).
- ✓ Le taux de change appliqué et sa date figurent dans la synthèse.

**Objectif** : exploiter des données imbriquées, les agréger, et combiner deux sources dans un même calcul.

---

## A.2 — La météo de tous les chantiers 🟡

**Le besoin**
> Une entreprise de construction gère quatre chantiers en Belgique. Chaque matin à 6h30, le
> responsable planning souhaite recevoir **un seul message** indiquant les chantiers « à risque » pour
> la journée : température minimale inférieure à 3 °C **ou** précipitations supérieures à 5 mm.
> Pour chaque chantier à risque, le message précise la raison et les valeurs prévues. S'il n'y a
> aucun chantier à risque, le message l'indique simplement. La liste des chantiers évoluera : en
> ajouter un ne doit demander qu'une modification à un seul endroit.

**Ressources**

| Chantier | Latitude | Longitude |
|---|---|---|
| Bruxelles — Tour Quai | 50.85 | 4.35 |
| Liège — Gare Nord | 50.63 | 5.57 |
| Gand — Port | 51.05 | 3.72 |
| Namur — Citadelle | 50.47 | 4.87 |

- Prévisions du jour : `https://api.open-meteo.com/v1/forecast?latitude=50.85&longitude=4.35&daily=temperature_2m_min,precipitation_sum&forecast_days=1&timezone=Europe/Brussels`
  (latitude et longitude à adapter pour chaque chantier).

**Résultat attendu**
- ✓ Le workflow se déclenche automatiquement chaque jour à 6h30.
- ✓ Il produit **un seul** item contenant le message récapitulatif.
- ✓ Le message liste uniquement les chantiers à risque, avec la raison ; sinon il contient
  « Aucun chantier à risque aujourd'hui ».
- ✓ Les deux cas (avec et sans chantier à risque) ont été testés.

**Objectif** : traiter une liste d'éléments avec un appel par élément, appliquer des règles métier, puis regrouper le résultat.

---

## A.3 — La relance des tâches en retard 🟡

**Le besoin**
> Un manager suit les tâches de son équipe dans un outil de gestion de projet. Il souhaite un point
> hebdomadaire : pour chaque collaborateur, le nombre de tâches **non terminées**. Les collaborateurs
> ayant **plus de 10 tâches ouvertes** doivent recevoir un message de relance personnalisé indiquant
> leur nom, leur nombre de tâches ouvertes et les intitulés de 3 d'entre elles. Les autres apparaissent
> dans un récapitulatif unique « équipe à jour » destiné au manager.

**Ressources**
- Tâches : `https://jsonplaceholder.typicode.com/todos` (champ `completed`, lien `userId`)
- Collaborateurs : `https://jsonplaceholder.typicode.com/users`

**Résultat attendu**
- ✓ Un message de relance par collaborateur concerné, avec son nom (et non son identifiant), son
  nombre de tâches ouvertes et 3 intitulés.
- ✓ Un seul item récapitulatif listant les autres collaborateurs et leur nombre de tâches ouvertes.
- ✓ Le total des tâches ouvertes de tous les collaborateurs correspond au nombre de tâches non
  terminées de la source.

**Objectif** : regrouper des données par personne et croiser deux sources sur une clé commune.

---

## A.4 — Le formulaire de contact du site web 🔴

**Le besoin**
> Une agence web souhaite que le formulaire de contact de son site envoie chaque demande (nom, email,
> message) à une adresse HTTP fournie par n8n. Chaque demande doit être **validée** (les trois champs
> sont présents, l'email a un format valide), **normalisée** (espaces superflus supprimés, email en
> minuscules), **horodatée** puis **enregistrée en base**. Le site doit toujours recevoir une réponse
> claire :
> - succès si la demande est enregistrée ;
> - erreur explicite si la demande est invalide, en précisant ce qui ne va pas ;
> - avertissement si cet email a déjà envoyé une demande : dans ce cas, rien n'est enregistré.

**Ressources**
- Table à créer :
  ```sql
  CREATE TABLE IF NOT EXISTS formation.contacts (
    id       SERIAL PRIMARY KEY,
    nom      TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE,
    message  TEXT NOT NULL,
    recu_le  TIMESTAMPTZ NOT NULL
  );
  ```
- Simulation du site avec `curl` (sous Windows PowerShell : `curl.exe`) ou Postman :
  ```bash
  curl -X POST "<adresse fournie par votre workflow>" \
    -H "Content-Type: application/json" \
    -d '{"nom": "  Alice Martin ", "email": " Alice.Martin@Exemple.be", "message": "Bonjour, je souhaite un devis."}'
  ```

**Résultat attendu**
- ✓ Une demande valide est enregistrée avec un email en minuscules, sans espaces superflus, et une
  date de réception ; le site reçoit un code **200**.
- ✓ Une demande invalide (champ manquant, email `alice@exemple`) n'est pas enregistrée ; le site reçoit
  un code **400** et un message indiquant le problème.
- ✓ Une deuxième demande avec le même email n'est pas enregistrée ; le site reçoit un code **409**.
- ✓ Le workflow fonctionne aussi en mode production (workflow publié, adresse définitive).

**Objectif** : exposer un workflow comme un service web, sécuriser les données entrantes et dialoguer avec une base de données.

---

## A.5 — La synchronisation du catalogue 🔴

**Le besoin**
> Un revendeur tient son propre catalogue dans un fichier CSV. Son fournisseur publie son catalogue en
> ligne. Chaque lundi matin, le revendeur souhaite un **rapport des écarts** entre les deux, limité aux
> produits de son catalogue :
> - les produits dont le **prix diffère** chez le fournisseur (ancien et nouveau prix) ;
> - les produits **en rupture de stock** chez le fournisseur ;
> - les produits **absents** du catalogue fournisseur.
>
> Les produits du fournisseur que le revendeur ne vend pas ne l'intéressent pas.

**Ressources**
- Catalogue interne : `/data/catalogue_interne.csv` (colonnes `id`, `titre`, `prix`)
- Catalogue fournisseur : `https://dummyjson.com/products?limit=0&select=title,price,stock`
  (le champ `id` correspond à la colonne `id` du catalogue interne)

**Résultat attendu**
- ✓ Le workflow se déclenche automatiquement chaque lundi à 7h.
- ✓ Un fichier `/data/ecarts_catalogue.csv` est produit, avec une ligne par écart et les colonnes
  `id`, `titre`, `type_ecart`, `prix_interne`, `prix_fournisseur`.
- ✓ `type_ecart` vaut `prix_modifie`, `rupture_fournisseur` ou `absent_fournisseur`.
- ✓ Aucun produit absent du catalogue interne n'apparaît dans le rapport.

**Objectif** : lire un fichier, comparer deux jeux de données et produire un rapport exploitable.

---

## A.6 — Défi : la veille des taux de change 🔴

**Le besoin**
> Une société d'import paie ses fournisseurs en dollars américains, livres sterling et francs suisses.
> Le service financier souhaite :
> 1. chaque jour ouvrable à 9h, relever le taux de l'euro face à ces trois devises et **l'historiser** en
>    base (un relevé par devise et par date, sans doublon si le workflow est relancé) ;
> 2. comparer chaque taux au **relevé précédent** et produire une alerte si une devise a varié de
>    **plus de 1 %** (devise, ancien taux, nouveau taux, variation en %) ;
> 3. ne jamais échouer en silence : si le service de taux ne répond pas, retenter quelques fois, puis
>    produire une alerte « service indisponible » ; toute autre erreur imprévue du workflow doit
>    aussi être signalée, avec le nom du workflow et le message d'erreur.

**Ressources**
- Taux du jour : `https://api.frankfurter.app/latest?from=EUR&to=USD,GBP,CHF`
- Taux d'une date passée (pour amorcer l'historique) : `https://api.frankfurter.app/2026-10-01?from=EUR&to=USD,GBP,CHF`
- Adresse renvoyant toujours une erreur (pour tester la panne) : `https://postman-echo.com/status/500`
- Table à créer :
  ```sql
  CREATE TABLE IF NOT EXISTS formation.taux_change (
    date_taux  DATE    NOT NULL,
    devise     CHAR(3) NOT NULL,
    taux       NUMERIC(12,6) NOT NULL,
    releve_le  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (date_taux, devise)
  );
  ```

**Résultat attendu**
- ✓ Après exécution, la table contient une ligne par devise pour la date du jour ; une seconde exécution
  le même jour ne crée pas de doublon.
- ✓ Avec un historique amorcé, une variation supérieure à 1 % produit une alerte détaillée ;
  sinon aucune alerte n'est produite.
- ✓ En remplaçant l'adresse du service par l'adresse d'erreur, le workflow ne s'arrête pas : il
  retente, puis produit l'alerte « service indisponible ».
- ✓ Une erreur imprévue sur le workflow publié déclenche un signalement contenant le nom du
  workflow et le message d'erreur.

**Objectif** : construire un traitement planifié fiable, avec historique en base et gestion des erreurs à plusieurs niveaux.
