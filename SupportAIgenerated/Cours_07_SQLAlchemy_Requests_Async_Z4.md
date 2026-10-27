# Cours personnel 07 — SQLAlchemy, Requests et programmation asynchrone

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Support principal :** `2026-08-17_21 - SQLAlchemy, requests et async.md`, dans `2026 Cours.zip` (notes reconstituées par un collègue à partir des dossiers de formation ; Cédric Van Osselaer, 17–18 août, puis Robin Pêcheur, 20–21 août 2026).  
**Références de travail :** dépôt GitHub `Mircea11/BF_IntegIA_2026` et export local du workflow n8n A.2.  
**Temps conseillé :** lecture 75–90 min ; 3 blocs de pratique de 45 min ; correction 20 min.  
**Prérequis :** cours 02 (fonctions et JSON), cours 03 (SQL), cours 06 (classes).  
**Objectif professionnel :** récupérer des données d'une API, les stocker sans erreur, puis organiser plusieurs opérations réseau de manière fiable.

> **Distinction de départ.** Ce cours explique ce qui figure dans le support de ton collègue et le relie à tes fichiers contrôlés sur GitHub. Un extrait présent dans ton dépôt ne prouve pas que tu l'as écrit ou expliqué seul. L'autonomie sera vérifiée par les exercices, sans IA pendant le premier essai.

## 1. Carte du module : à quoi servent ces outils ?

Un même flux de données peut mobiliser quatre technologies différentes :

1. **`requests`** lit une API externe ou locale (HTTP → réponse JSON).
2. **Python** vérifie et transforme les réponses (listes/dictionnaires → données métier).
3. **SQLAlchemy Core ou ORM** enregistre et relit les données (Python ↔ SQL ↔ base).
4. **`asyncio`** organise plusieurs attentes simultanées lorsqu'une application doit contacter de nombreuses API.

Le module de ton collègue suit cet ordre : SQLAlchemy Core ; `requests` ; exercice météo des communes bruxelloises ; SQLAlchemy ORM ; `asyncio` et comparaison avec threads/processus. Son support précise qu'il est **reconstitué à partir des dossiers de code** et non de notes manuscrites ; les affirmations sur les notebooks de cours ne constituent pas une vérification directe de ton Z4.

| Outil | Question à laquelle il répond | Exemple de ton travail | Usage vérifié ? |
|---|---|---|---|
| `requests` | « Comment interroger un service ? » | `app.py` du conseiller B5 | Oui, présence du code |
| `psycopg` | « Comment exécuter du SQL en Python ? » | Historique B5, tables `b5_messages` et `b5_profile` | Oui, présence du code |
| SQLAlchemy Core | « Comment utiliser un moteur, des connexions et des transactions ? » | Alternative pédagogique à `psycopg` | Notion du cours ; pas de refonte démontrée dans B5 |
| SQLAlchemy ORM | « Comment représenter une ligne par un objet ? » | Produit / catégorie, exercice de formation | Notion du cours ; non prouvé en usage autonome |
| `asyncio` | « Comment attendre plusieurs opérations réseau sans tout sérialiser ? » | Futurs appels API parallèles | Notion du cours ; maîtrise à tester |
| n8n HTTP Request | « Comment automatiser des appels sans tout coder ? » | A.2 météo, B5 | Workflow local disponible ; pas un usage direct de `requests` |

**Erreur à éviter :** `requests`, SQLAlchemy et `asyncio` ne font pas le même travail et ne sont pas interchangeables.

## 2. SQLAlchemy Core : connexion et requêtes

### 2.1 Base de données, pilote, moteur et connexion

**Base** : PostgreSQL, SQLite ou SQL Server. **Pilote** : bibliothèque qui dialogue avec la base (`psycopg`, `pysqlite`, `pyodbc`). **Engine** : point d'accès SQLAlchemy qui gère les connexions et leur réutilisation. **Connection** : liaison empruntée à l'engine pour exécuter une requête.

```python
from sqlalchemy import create_engine, text

# Exemple autonome : base SQLite en mémoire, sans installer PostgreSQL.
engine = create_engine("sqlite+pysqlite:///:memory:")

with engine.begin() as conn:
    conn.execute(text("CREATE TABLE produit (id INTEGER PRIMARY KEY, nom TEXT, stock INTEGER)"))
    conn.execute(
        text("INSERT INTO produit (id, nom, stock) VALUES (:id, :nom, :stock)"),
        [
            {"id": 1, "nom": "Ballon", "stock": 0},
            {"id": 2, "nom": "Raquette", "stock": 5},
        ],
    )

with engine.connect() as conn:
    lignes = conn.execute(
        text("SELECT nom, stock FROM produit WHERE stock > :minimum"),
        {"minimum": 0},
    ).all()

print(lignes)  # [('Raquette', 5)]
```

Ce programme illustre `create_engine`, `text`, les **paramètres liés** et deux types de blocs : `engine.begin()` valide les changements si tout se passe bien ; `engine.connect()` exige un `commit()` pour enregistrer les changements. Un simple `SELECT` n'a normalement rien à enregistrer.

**Différence par rapport à ton B5 :** [`app.py`, lignes 44–85](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py#L44-L85) utilise `psycopg.connect(...)` et des marqueurs `%s`, pas SQLAlchemy. Le résultat métier peut être comparable ; l'interface de programmation diffère.

### 2.2 Comprendre `commit`, `rollback` et les transactions

Une **transaction** regroupe des opérations qui doivent réussir ensemble. Avec `engine.begin()`, si une exception survient, les opérations non validées sont annulées. Cela évite de laisser des données partiellement enregistrées.

```python
from sqlalchemy import text

try:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO produit VALUES (3, 'Tasse', 8)"))
        conn.execute(text("INSERT INTO produit VALUES (3, 'Doublon', 1)"))
except Exception as exc:
    print(type(exc).__name__)  # contrainte UNIQUE / PRIMARY KEY

# La ligne 3 n'est pas conservée : la transaction a échoué.
with engine.connect() as conn:
    print(conn.execute(text("SELECT count(*) FROM produit WHERE id=3")).scalar_one())  # 0
```

**Contrôle métier :** dans une base de ventes, une commande et ses lignes doivent être cohérentes. Enregistrer seulement la moitié serait une anomalie. Les frontières de transaction ont donc un effet sur la qualité des données et des rapports.

### 2.3 Paramètres liés et sécurité

```python
nom = "Forest"

# Dangereux : la valeur devient du texte SQL.
# conn.execute(text(f"SELECT * FROM commune WHERE nom = '{nom}'"))

# Correct : la valeur est un paramètre, traité séparément du SQL.
conn.execute(text("SELECT * FROM commune WHERE nom = :nom"), {"nom": nom})
```

L'injection SQL survient lorsqu'une entrée extérieure modifie la **structure** de la requête. Les paramètres liés évitent d'interpréter une valeur utilisateur comme du SQL. Dans `psycopg`, on utilise `WHERE session_id=%s` avec `(session,)`, comme dans B5.

**Règle pratique :** n'assemble jamais une requête avec `f"...{valeur_utilisateur}..."` pour des valeurs de données. Les noms de tables et de colonnes demandent une validation spécifique ; les paramètres ne les remplacent pas.

### 2.4 Pandas et SQLAlchemy

```python
import pandas as pd
from sqlalchemy import text

with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT nom, stock FROM produit WHERE stock >= :seuil"),
        conn,
        params={"seuil": 0},
    )
print(df)
```

`pd.read_sql` sert à **lire des données sous forme de tableau**. Pour un `DROP TABLE`, un `UPDATE` ou un `INSERT`, on préfère exécuter l'instruction via SQLAlchemy, avec transaction explicite. `DataFrame.to_sql(..., if_exists="replace")` peut supprimer et recréer une table : ne jamais l'utiliser sur une vraie base sans comprendre les conséquences.

## 3. `requests` : communiquer avec une API

### 3.1 Les trois étapes d'un appel fiable

Un appel HTTP comprend : **la demande** (URL, paramètres, méthode) ; **la réponse** (code HTTP, en-têtes, contenu) ; **les contrôles** (erreurs, délai, structure des données).

```python
import requests

url = "https://dummyjson.com/products"

try:
    reponse = requests.get(
        url,
        params={"limit": 5, "select": "id,title,price,stock"},
        timeout=10,
    )
    reponse.raise_for_status()
    data = reponse.json()
    produits = data["products"]
    print("Produits reçus :", len(produits))
except requests.exceptions.RequestException as exc:
    print("Appel HTTP échoué :", type(exc).__name__)
except (ValueError, KeyError, TypeError) as exc:
    print("Réponse non conforme :", type(exc).__name__)
```

`params=` construit les paramètres d'URL ; `timeout=10` évite une attente indéfinie ; `raise_for_status()` signale les réponses d'erreur HTTP ; `.json()` transforme le JSON en structures Python mais **ne valide pas** automatiquement ton schéma métier.

| Code | Signification habituelle | Réflexe |
|---|---|---|
| 200 | Succès | Contrôler aussi le contenu |
| 400 | Demande invalide | Corriger les paramètres |
| 401 / 403 | Non authentifié / interdit | Vérifier les droits, ne pas publier les clés |
| 404 | Ressource absente | Vérifier URL et identifiant |
| 429 | Trop de requêtes | Réduire la cadence et respecter les limites |
| 500 / 503 | Service indisponible | Journaliser, éventuellement réessayer prudemment |

**Référence réelle :** [`B5/app.py`, lignes 30–41](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py#L30-L41) crée `requests.Session()` et centralise `timeout`, `raise_for_status()` et `.json()` dans `req(method, url, **kwargs)`. Ton application interroge DummyJSON, Qdrant et les API locales vLLM. Ces appels sont synchrones dans le code contrôlé.

### 3.2 GET et POST ne se confondent pas

`GET` demande une ressource. `POST` envoie des données à un service et peut déclencher un traitement ou une création : il n'est **pas automatiquement sans effet secondaire**. Par exemple, le `/reindex` de B5 est une requête POST qui lance une réindexation.

```python
# Exemple illustratif : schéma de requête, NE PAS lancer sans service cible.
# requests.post(url, json={"session_id": "demo", "message": "Bonjour"}, timeout=10)
```

**Attention aux prix et stocks :** dans B5, la recommandation doit utiliser les produits existants et vérifier le stock actuel. Une belle réponse du modèle ne suffit pas : c'est le contrôle des données qui rend la réponse fiable.

### 3.3 Application du support : météo des 19 communes bruxelloises

Le support propose de récupérer les communes et coordonnées (ODWB), d'interroger Open-Meteo, d'aplatir les données heure × commune puis de remplir `commune` et `meteo`. Le schéma est **une dimension et une table de faits** :

- `commune(code_ins PRIMARY KEY, nom, latitude, longitude)` : une ligne par commune ;
- `meteo(code_ins, date_heure, temperature, pluie_probabilite)` : une ligne par commune et heure ; clé composée `(code_ins, date_heure)` ; clé étrangère vers `commune`.

Les localités doivent être dédoublonnées par **code INS**, et non par leur simple libellé. Une jointure permet ensuite de produire une série temporelle pour Forest ou un tableau comparatif pour les 19 communes.

**Ton lien réel :** l'export local `A2_Meteo_Chantiers_n8n.json` contient le nœud `03 - Open-Meteo par chantier`, suivi de l'évaluation des seuils et du regroupement des résultats. Il illustre la **même idée d'appel à une API**, mais dans n8n et sur des chantiers plutôt que dans un programme Python sur les communes. Ce fichier a été vérifié dans tes fichiers disponibles ; je ne lui attribue pas de lien GitHub non confirmé.

## 4. SQLAlchemy ORM : traduire les lignes en objets

Dans le **Core**, tu écris la requête ; dans l'**ORM**, tu déclares des classes correspondant aux tables. Une instance `Produit(...)` peut alors représenter un enregistrement.

### 4.1 Exemple minimum et exécutable (SQLite)

```python
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Categorie(Base):
    __tablename__ = "categorie"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(60))
    produits: Mapped[list["Produit"]] = relationship(back_populates="categorie")

class Produit(Base):
    __tablename__ = "produit"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    categorie_id: Mapped[int] = mapped_column(ForeignKey("categorie.id"))
    categorie: Mapped["Categorie"] = relationship(back_populates="produits")

engine_orm = create_engine("sqlite+pysqlite:///:memory:")
Base.metadata.create_all(engine_orm)

with Session(engine_orm) as session:
    sport = Categorie(id=1, nom="Sport")
    session.add_all([sport, Produit(id=10, nom="Raquette", categorie=sport)])
    session.commit()

with Session(engine_orm) as session:
    produits = session.scalars(select(Produit)).all()
    print([(p.nom, p.categorie.nom) for p in produits])  # [('Raquette', 'Sport')]
```

**À expliquer :** `Mapped` indique les champs ; `mapped_column(primary_key=True)` fixe une clé ; `ForeignKey` matérialise la relation dans la base ; `relationship` permet une navigation Python entre objets ; `Session` suit les changements et pilote les transactions.

Le support du collègue utilise aussi `MappedAsDataclass` afin de générer certains comportements des instances. Nous commençons par **`DeclarativeBase` seul**, plus simple, puis reviendrons aux dataclasses lorsque les relations seront comprises. C'est un choix pédagogique explicite, pas une reproduction exacte de tous ses exemples.

### 4.2 Session, CRUD et repository

`session.add(...)` prépare un ajout ; `session.scalars(select(...))` lit les objets ; modifier un attribut puis valider crée une mise à jour ; `session.delete(...)` prépare une suppression. `session.rollback()` annule les modifications non validées.

Le support présente un `ProductRepository` : une classe dont les méthodes `add`, `get_all` et `delete` centralisent l'accès aux données. **Intérêt :** isoler la logique de stockage du reste de l'application. **Limite :** ajouter un ORM à une petite application peut accroître sa complexité ; ne migre pas B5 simplement pour utiliser une nouveauté du cours.

`Base.metadata.create_all()` crée les tables manquantes ; il **ne réalise pas des migrations de schéma**. Pour faire évoluer une base existante, des migrations (par exemple Alembic) sont nécessaires, hors du périmètre pratique de ce cours.

## 5. `asyncio` : exploiter le temps d'attente

### 5.1 Synchrone contre asynchrone

```python
import time
import asyncio

# 1) Bloquant : environ 3 secondes.
def operation_sync(nom, secondes):
    time.sleep(secondes)
    return nom

start = time.perf_counter()
print([operation_sync("A", 2), operation_sync("B", 1)])
print("Synchrone :", round(time.perf_counter() - start, 2), "s")

# 2) Concurrent : environ 2 secondes sur ces attentes simulées.
async def operation_async(nom, secondes):
    await asyncio.sleep(secondes)
    return nom

async def main():
    return await asyncio.gather(operation_async("A", 2), operation_async("B", 1))

start = time.perf_counter()
print(asyncio.run(main()))  # dans un script Python, pas une cellule Jupyter déjà asynchrone
print("Asynchrone :", round(time.perf_counter() - start, 2), "s")
```

**Pourquoi le gain ?** `await` rend le contrôle à la boucle d'événements pendant l'attente ; l'autre tâche peut avancer. Ce n'est **pas** un calcul mathématique parallèle. Dans un notebook Jupyter, utiliser `await main()` plutôt qu'`asyncio.run(main())` si une boucle est déjà active.

**Piège explicite du support :** `time.sleep()` à l'intérieur d'une fonction `async def` bloque la boucle. Utiliser `await asyncio.sleep()` pour simuler l'attente, et de vrais clients asynchrones (`httpx.AsyncClient`, `aiohttp`, pilotes SQL async) pour les opérations réseau.

### 5.2 Les outils essentiels

| Outil | Fonction | Point de vigilance |
|---|---|---|
| `await coro()` | Attendre une coroutine | Doit se trouver dans une fonction `async` (hors particularités notebook) |
| `asyncio.gather(a(), b())` | Lancer et attendre plusieurs coroutines | Ne limite pas seul le nombre d'appels |
| `asyncio.create_task(coro())` | Programmer une tâche | Conserver sa référence et récupérer son résultat |
| `asyncio.wait_for(coro(), 3)` | Imposer un délai maximal | Peut annuler l'opération en cas de délai dépassé |
| `asyncio.Semaphore(5)` | Limiter les opérations simultanées | Protège API et ressources |
| `asyncio.TaskGroup()` | Grouper les tâches et gérer leurs échecs | Gestion d'erreurs structurée ; Python ≥3.11 |
| `asyncio.to_thread(...)` | Déporter une fonction bloquante dans un thread | N'en fait pas une API nativement asynchrone |

### 5.3 Limiter les appels et capturer les erreurs

```python
import asyncio

async def traiter(i, semaphore):
    async with semaphore:
        await asyncio.sleep(0.1)  # Simulation d'un appel réseau.
        return {"id": i, "statut": "ok"}

async def programme():
    limite = asyncio.Semaphore(3)
    return await asyncio.gather(*(traiter(i, limite) for i in range(10)))

if __name__ == "__main__":
    print(asyncio.run(programme()))
```

Dans une application réelle, ajouter une stratégie adaptée pour les erreurs HTTP et les réponses 429 ; ne pas lancer des dizaines d'appels externes sans limite.

### 5.4 Threads et processus

| Approche | Bonne utilisation | Mauvaise intuition |
|---|---|---|
| `asyncio` | Beaucoup d'opérations réseau qui attendent | « Rend automatiquement le CPU plus rapide » |
| Threads | Exécuter une fonction bloquante sans figer l'interface | « Accélère forcément un calcul Python pur » |
| Processus | Calcul CPU lourd réparti sur plusieurs cœurs | « Même coût mémoire qu'une simple coroutine » |

**Note de précision :** le support décrit le GIL de CPython et ses effets usuels. Les possibilités de Python évoluent ; pour ce parcours, retiens surtout le choix pratique selon que le travail est **I/O-bound** (attentes) ou **CPU-bound** (calculs).

### 5.5 `*` et `**` : le dépaquetage

```python
arguments = ["A", 1]
print(*arguments)                  # A 1
options = {"timeout": 10}
# requests.get(url, **options)    # équivalent à requests.get(url, timeout=10)
# await asyncio.gather(*(tache(i) for i in range(10)))
```

`*` développe une séquence en arguments positionnels ; `**` développe un dictionnaire en arguments nommés. Ne pas nommer une variable `list`, `dict` ou `str` : on masquerait les fonctions intégrées de Python.

## 6. Ce que tu as déjà utilisé — et ce qu'il reste à prouver

| Preuve | Présent dans le travail | Exercice de compétence indépendante |
|---|---|---|
| Lire du JSON issu d'API | B5 `req()` ; workflow n8n A.2 | Expliquer `status_code`, `timeout`, `raise_for_status`, erreurs JSON |
| Insérer et lire du SQL | B5 `remember()` / `recent()` via psycopg | Reproduire une requête paramétrée en SQLAlchemy Core |
| Manipuler des classes | B5 `ChatIn(BaseModel)` ; cours 06 | Écrire un ORM minimal et définir la relation 1–N |
| Coordonner plusieurs appels | n8n orchestre déjà des nœuds | Écrire deux coroutines et expliquer `gather` / `Semaphore` |
| Mesurer la fiabilité | B5 tests simulés et contrôle des stocks | Tester erreurs, délais, doublons et rollback sans assistance |

**Décision pédagogique :** ne pas transformer tes workflows n8n ni l'application B5 avant d'avoir démontré ces cinq compétences. Nous visons la compréhension du code existant, pas un nouveau projet parallèle.

## 7. Trois séances de 45 minutes (travail sans IA au premier essai)

### Bloc A — SQLAlchemy Core : une transaction et une requête (45 min)

**But :** écrire un script `cours07_core.py` avec une base SQLite en mémoire, sans toucher à PostgreSQL sur ton Z4.

1. Créer la table `produit(id, nom, stock)`.
2. Insérer `Ballon (0)`, `Raquette (5)`, `Tasse (3)` par paramètres liés.
3. Afficher uniquement les produits de stock strictement positif.
4. Provoquer volontairement un doublon d'identifiant **dans une transaction distincte**, constater qu'il n'est pas conservé.
5. Expliquer pourquoi `engine.begin()` est utilisé pour écrire.

**Critère de réussite :** les deux produits disponibles sont affichés ; une erreur d'insertion n'altère pas les lignes déjà validées. Marquer chaque opération « seul », « avec aide » ou « non réalisé ».

### Bloc B — `requests` : qualité des réponses (45 min)

**But :** écrire `cours07_api.py`. Lire cinq produits DummyJSON avec paramètres (`limit`, `select`) ; extraire `id`, `title`, `price`, `stock`. Vérifier le type de `products`, les clés obligatoires et la cohérence du stock. Afficher les noms des produits disponibles, sans inventer la devise.

**Variante hors ligne :** si l'API ne répond pas, travailler avec un petit fichier JSON créé manuellement ; c'est la compétence de validation JSON qui importe. Ne jamais copier un jeton API dans GitHub.

**Critère de réussite :** erreurs HTTP et erreurs de structure distinguées ; absence de proposition comme « disponible » quand le stock manque.

### Bloc C — `asyncio` : attente, mesure et contrôle (45 min)

**But :** écrire `cours07_async.py`, entièrement hors réseau.

1. Mesurer deux attentes séquentielles de 2 et 1 seconde.
2. Mesurer les mêmes attentes via `asyncio.gather`.
3. Lancer dix simulations sous `Semaphore(3)`.
4. Remplacer temporairement `await asyncio.sleep` par `time.sleep` dans une coroutine ; observer et expliquer le problème, puis corriger.

**Critère de réussite :** expliquer la différence entre concurrence sur attente et parallélisme CPU, sans employer « multithreading » comme synonyme de `asyncio`.

**Option ultérieure :** reproduire le schéma `commune` / `meteo` du support avec une API et une base de test, seulement après validation des trois blocs.

## 8. Autotest — 10 questions (sans consulter la correction)

1. Dans SQLAlchemy, quelle différence entre `Engine`, `Connection` et `Session` ?
2. Pourquoi `:nom` est-il préférable à une f-string pour construire un `WHERE` ?
3. Que se passe-t-il si une transaction `engine.begin()` échoue à mi-parcours ?
4. Quelle différence entre `requests.get(..., params=...)` et `requests.post(..., json=...)` ?
5. À quoi servent ensemble `timeout`, `raise_for_status()` et `.json()` ?
6. Quelle différence entre `ForeignKey` et `relationship` dans l'ORM ?
7. Pourquoi `Base.metadata.create_all()` ne remplace-t-il pas des migrations ?
8. Pourquoi `asyncio.gather` peut-il traiter deux attentes en moins de temps qu'une suite synchrone ?
9. Pourquoi `time.sleep()` est-il dangereux à l'intérieur de `async def` ?
10. Quels trois contrôles effectuer avant de publier une recommandation issue d'une API catalogue ?

### Correction et critères

1. `Engine` prépare/gère les connexions ; `Connection` exécute le SQL ; `Session` représente l'unité de travail ORM et suit les objets.
2. Les paramètres liés transportent les valeurs séparément du code SQL et empêchent une entrée utilisateur de modifier sa structure.
3. Elle est annulée : aucune modification non validée du bloc n'est conservée.
4. `GET` demande des données avec des paramètres d'URL ; `POST` envoie un corps JSON et peut produire un effet sur le serveur.
5. Limiter l'attente, signaler les erreurs HTTP, puis décoder la réponse ; la validation métier reste nécessaire.
6. `ForeignKey` impose un lien dans la base ; `relationship` facilite la navigation entre objets Python.
7. Il crée les tables absentes, mais ne migre pas les structures existantes.
8. Les coroutines peuvent avancer durant les temps d'attente les unes des autres.
9. Il bloque la boucle d'événements ; utiliser `await asyncio.sleep()` pour les pauses simulées.
10. Identifiant présent dans le catalogue ; disponibilité vérifiée ; prix et autres attributs correspondant aux données effectivement reçues.

**Interprétation du score :** 0–5/10, revoir les concepts ; 6–8/10, refaire les trois scripts ; 9–10/10 **et** les trois scripts produits sans IA, niveau opérationnel de base. Ce score n'est pas une certification ; c'est un contrôle personnel.

## 9. Sources et limites de vérification

**Support de ton collègue** (source pédagogique, fourni dans `2026 Cours.zip`) :  
`2026-08-17_21 - SQLAlchemy, requests et async.md` — cas SQLAlchemy Core, météo des communes bruxelloises, ORM, asyncio, erreurs de notebooks relevées par le collègue. Son dépôt `IA` n'est pas présenté ici comme audité.

**Ton GitHub, vérifié le 26 octobre 2026 :**

- [`N8N/B5_conseiller_produit_v2/app.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py) — fonctions `req`, `db`, `remember`, `recent`, gestion de la mémoire.
- [`N8N/B5_conseiller_produit_v2/README_SETUP_FR.md`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md) — architecture du prototype, points d'entrée et limites des tests.
- [`N8N/B5_conseiller_produit_v2/test_b5.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py) — tests simulés ; ne constituent pas une preuve de déploiement réel.

**Fichier local vérifié :** `A2_Meteo_Chantiers_n8n.json` — workflow météo n8n utilisant un nœud Open-Meteo. Il n'a pas été confirmé comme publié dans le dépôt distant.

**Documentation de référence (compléments vérifiés, distincts du support de cours) :**

- [SQLAlchemy 2.0 — transactions et connexion](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html)
- [Requests — Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
- [Python — asyncio (documentation officielle)](https://docs.python.org/3/library/asyncio-task.html)

**Prudence :** les exemples de produit, de temps et de catégories de ce cours sont pédagogiques. Ce document n'affirme ni avoir exécuté les scripts sur le Z4, ni avoir modifié PostgreSQL ou les workflows existants.

---

**Prochain cours (08) :** Polars et formats colonnaires — approfondir les transformations de données et comprendre les formats analytiques, à partir du support du 24 août 2026.
