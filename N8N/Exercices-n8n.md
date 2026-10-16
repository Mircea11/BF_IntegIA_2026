# Exercices — Formation n8n

Recueil d'énoncés à réaliser **soi-même** dans n8n. Chaque exercice décrit un **objectif** (et, pour
les use cases, un **besoin client**) : à vous de concevoir le pipeline — choisir le trigger, les
nodes, les brancher et le tester.

**Progression.** Modules 1-2 = *découvrir un node à la fois*. Module 3 = *logique & robustesse*.
Modules 4-5 = *use cases* (« un client décrit son besoin, automatisez-le »).

**Difficulté.** 🟢 facile · 🟡 moyen · 🔴 difficile.

---

## Boîte à outils (données & APIs disponibles)

**Fichiers de données** (déjà montés dans le conteneur sous `/data/`) :
- `/data/test.csv` — 3 personnes (`nom, ville, age`) → exercices débutants.
- `/data/Exercices_Pandas_athlete_events.csv` — 271 000 lignes (athlètes olympiques :
  `Name, Sex, Age, Team, NOC, Year, Season, Sport, Event, Medal`) → filtres, agrégations, lots.

**APIs publiques sans authentification** (utilisables directement dans un node HTTP Request) :

| Service | URL d'exemple | Contenu |
|---|---|---|
| Cat Facts | `https://catfact.ninja/fact` | Réponse JSON simple |
| Agify | `https://api.agify.io?name=alice` | Âge estimé d'un prénom |
| JSONPlaceholder | `https://jsonplaceholder.typicode.com/users/1` | Utilisateurs / posts factices |
| REST Countries | `https://restcountries.com/v3.1/name/belgium` | Données pays |
| Open-Meteo | `https://api.open-meteo.com/v1/forecast?latitude=50.85&longitude=4.35&current=temperature_2m` | Météo (Bruxelles) |
| GitHub | `https://api.github.com/users/torvalds` | Profil public (dépôts, abonnés) |
| Postman Echo | `https://postman-echo.com/get` | Renvoie la requête reçue (tester une credential) |
| Postman Echo (erreur) | `https://postman-echo.com/status/500` | Force une erreur HTTP 500 (robustesse) |

> ℹ️ n8n tourne sous Linux : utilisez les chemins `/data/...`, jamais `C:\...`.

---

# Module 1 — Découverte des nodes

*But : manipuler l'interface et comprendre qu'un node reçoit et renvoie une liste d'items JSON.*

### 1.1 — Le premier trigger 🟢
Créez un workflow qui démarre par un **Manual Trigger**, exécutez-le et décrivez ce qu'un trigger
renvoie. *Résultat attendu :* vous savez lire le panneau d'exécution et dire ce que produit le node.

### 1.2 — Produire de la donnée 🟢
Faites en sorte qu'un node **Manual Trigger** produise un item contenant `prenom`, `ville` et une `date`
qui se met à jour à chaque exécution. *Résultat attendu :* un item JSON structuré avec une date dynamique.

### 1.3 — Ajouter des champs 🟢
Reprenez le workflow de l'exercice précédent et ajouter des champs "Nom" et "Date de naissance" ,
puis explorez la réponse. *Résultat attendu :* 

### 1.4 — Enchaîner et documenter 🟡
Construisez un workflow qui récupère un utilisateur (`.../users/1`), n'en conserve que **2 champs**
(nom + email), avec des nodes **renommés**, une **Sticky Note** explicative, et la sortie du HTTP Request
**épinglée** pour itérer sans rappeler l'API. *Résultat attendu :* un workflow lisible et une sortie propre à 2 champs.

---

# Module 2 — Données, expressions & credentials

*But : transformer la donnée avec précision, écrire des expressions, router, et s'authentifier proprement.*

### 2.1 — Nettoyer une réponse d'API 🟢
À partir d'une réponse riche (`.../users/2`), ne conservez que **3 champs bien nommés** (dont la donnée
d'entreprise, imbriquée). *Résultat attendu :* une sortie ne contenant que ces trois champs.

### 2.2 — Premières expressions 🟡
À partir d'items contenant `prenom`, `nom`, `age`, calculez : un `nom_complet` en majuscules, une
`categorie` (« adulte » / « mineur » selon l'âge), et une `echeance` = aujourd'hui + 7 jours (format
`jj/mm/aaaa`). *Résultat attendu :* trois nouveaux champs, une valeur par item.

### 2.3 — Router selon une condition 🟡
En repartant de `/data/test.csv`, aiguillez les personnes : d'abord avec un **IF** (âge ≥ 30 ou non),
puis avec un **Switch** (par ville), puis avec un **Filter** (ne garder que les âges > 30). *Résultat
attendu :* vous savez dire quand utiliser IF, Switch ou Filter.

### 2.4 — Une credential sécurisée 🟡
Créez une credential **Header Auth** (`X-Api-Key`), nommez-la clairement (`service · compte · env`),
et utilisez-la dans un HTTP Request vers Postman Echo. *Résultat attendu :* l'en-tête est bien envoyé,
et aucun secret n'apparaît en clair dans le node.

### 2.5 — Message de bienvenue 🟡
**Besoin.** *« À chaque nouvel inscrit, préparer un message de bienvenue personnalisé prêt à envoyer. »*
Récupérez un utilisateur et construisez un champ `message` mêlant texte figé et données de la personne.
*Résultat attendu :* un item avec un seul champ `message` entièrement personnalisé.

---

# Module 3 — Logique, flux & robustesse

*But : recombiner des flux, traiter par lots, écrire de la logique sur-mesure, fiabiliser, factoriser.*

### 3.1 — Joindre deux sources 🟡
**Besoin.** *« J'ai mes clients d'un côté, mes commandes de l'autre (clé commune `id`). Je veux chaque
commande enrichie du nom du client. »* Réunissez les deux sources avec un **Merge** ; comparez ensuite
les modes (jointure sur clé, empilage, appariement par position). *Résultat attendu :* les commandes
sont enrichies du nom, et vous savez expliquer le sort des enregistrements non appariés.

### 3.2 — Traiter par lots 🟡
**Besoin.** *« J'ai un gros fichier ; je dois appeler un service pour chaque ligne, mais l'API a un
quota : il faut y aller par petits paquets avec une pause. »* À partir du CSV des athlètes (limité à
~20 lignes), traitez les items **par lots** avec une temporisation. *Résultat attendu :* les items sont
traités en plusieurs lots et la boucle s'arrête d'elle-même.

### 3.3 — Dédoublonner une liste 🟡
**Besoin.** *« Ma liste de contacts contient des doublons d'email ; je veux une liste unique avant import
CRM. »* Supprimez les doublons sur le champ `email`. *Résultat attendu :* un seul contact par email en sortie.

### 3.4 — Rendre un workflow robuste 🔴
**Besoin.** *« Mon automatisation appelle une API qui tombe parfois. Je ne veux pas que tout s'arrête en
silence : réessayer, isoler l'échec, et être prévenu. »* Sur un appel qui échoue à coup sûr
(`postman-echo.com/status/500`), mettez en place une stratégie de robustesse (réessais, gestion de la
branche d'erreur, workflow d'alerte). *Résultat attendu :* l'échec n'interrompt plus le workflow et il est journalisé.

### 3.5 — Factoriser en sous-workflow 🔴
**Besoin.** *« Plusieurs de mes workflows doivent nettoyer et valider un contact de la même façon. Je veux
une brique unique, réutilisable et testable à part. »* Isolez la logique « normaliser + valider un contact »
dans un sous-workflow appelé depuis un workflow parent. *Résultat attendu :* la brique fonctionne seule et
appelée par le parent.

---

# Module 4 — Use cases intégrés

*But : concevoir un workflow complet à partir d'un besoin client. À vous de choisir trigger et nodes.*

### 4.1 — Présélection de candidats 🔴
**Besoin.** *« Nous recevons des candidatures (nom, email, pseudo GitHub, années d'expérience). Je veux
automatiquement : ne garder que les profils d'au moins 3 ans, enrichir chaque profil retenu avec son
activité GitHub publique (dépôts, abonnés), et préparer un court message de shortlist par candidat. »*
*Résultat attendu :* un item par candidat retenu, enrichi, avec un message de shortlist.

### 4.2 — Chiffre d'affaires par produit 🟡
**Besoin.** *« Voici mes commandes du jour (produit + montant). Je veux un récap : le CA total par produit
et le total général, prêt à coller dans un email. »* *Résultat attendu :* un CA par produit, un total
général, et un court rapport texte.

### 4.3 — Palmarès olympique 🔴
**Besoin.** *« À partir de l'historique des JO, sortez-moi, pour un pays et une année donnés (ex. France
2012), uniquement les athlètes médaillés, dans un fichier propre : nom, sport, épreuve, médaille. »*
Source : `/data/Exercices_Pandas_athlete_events.csv`. *Résultat attendu :* un fichier exporté ne contenant
que les médaillés demandés.

### 4.4 — Alerte météo quotidienne 🟡
**Besoin.** *« Chaque matin, préviens-moi s'il va faire froid à Bruxelles (< 5 °C). Et si l'API météo ne
répond pas, ne plante pas en silence. »* *Résultat attendu :* un workflow planifié qui n'alerte que sous
le seuil et qui résiste à une panne de l'API.

---

# Module 5 — Agents IA *(prospectif — « Jour 5 »)*

*But : construire un agent IA. Prérequis : une credential LLM (OpenAI/Anthropic, ou Ollama en local).*
*Fil rouge : les sous-workflows du module 3 deviennent des **outils** de l'agent.*

### 5.1 — Votre premier agent 🟢
Assemblez un agent conversationnel (déclencheur de chat + agent + modèle de langage) et donnez-lui un rôle
via un prompt système. *Résultat attendu :* l'agent répond dans le ton et la langue demandés.

### 5.2 — Donner un outil à l'agent 🟡
Exposez le sous-workflow « normaliser & valider un contact » (exercice 3.5) comme **outil** de l'agent, en
le décrivant clairement. *Résultat attendu :* l'agent appelle l'outil quand on lui demande de nettoyer un contact.

### 5.3 — Donner de la mémoire 🟡
Ajoutez une **mémoire de conversation** à l'agent, puis vérifiez qu'il se souvient d'une information donnée
au message précédent. *Résultat attendu :* l'agent maintient le contexte au sein d'une session.

### 5.4 — RAG : répondre depuis vos documents 🔴
**Besoin.** *« Je veux un assistant qui répond à partir de NOS documents, pas de ses connaissances
générales. »* Indexez quelques documents dans un vector store (pgvector de `docker/`, ou store en mémoire),
puis laissez l'agent y chercher. *Résultat attendu :* l'agent répond en s'appuyant sur les documents indexés.

### 5.5 — Assistant support client (synthèse) 🔴
**Besoin.** *« Un assistant de support par chat qui : (1) répond aux questions produit depuis notre doc (RAG),
(2) sait normaliser/valider un contact pour ouvrir un ticket (outil), (3) garde le fil de la conversation
(mémoire), et (4) ne s'effondre pas si un service tombe (robustesse). »* *Résultat attendu :* un agent unique
combinant RAG, outil, mémoire et gestion d'erreurs.
