# Cours personnel 02 — Python pour la data science : comprendre ton code existant

**Parcours : AI Integration Specialist — consolidation au 26 octobre 2026**  
**Lecture : 70–90 minutes | Pratique : 3 × 45 minutes (répartissables)**  
**Support de référence :** `2026-05 - Python pour la data science.md` dans `2026 Cours.zip` (notes du collègue, mai 2026).  
**Complément :** `2026-08-03_10 - Bases Python et visualisation.md` (août 2026).  
**Projet réel :** `Mircea11/BF_IntegIA_2026`, branche `main`, état consulté le 26/10/2026.

> **But** — Pouvoir lire, expliquer et modifier sans assistance les blocs Python simples déjà présents dans tes projets B5 et RAG. La maîtrise de NumPy, pandas et scikit-learn ne doit pas être supposée au seul motif que les modules ont été vus en formation.

## 1. Cartographie : où se trouve Python dans ton travail ?

Tu pars d'une expérience solide en prévisions, planification et analyse. Python automatise des tâches que tu connais déjà : charger des sources, vérifier les données, faire des calculs, produire des résultats traçables. Il n'est pas nécessaire de te présenter comme « développeur IA » pour expliquer cette valeur.

| Élément vérifié | Fichier GitHub | Compétence à expliquer | État constaté |
|---|---|---|---|
| Backend du conseiller B5 | `N8N/B5_conseiller_produit_v2/app.py` | fonctions, dictionnaires, HTTP, erreurs, configuration | Code présent ; autonomie d'écriture non établie |
| Tests du conseiller B5 | `N8N/B5_conseiller_produit_v2/test_b5.py` | tests unitaires, simulation, assertions | Suite de tests présente ; exécution indépendante à confirmer |
| Extraction de documents | `RAG/.../rag/demo/01_intro.ipynb` | `Path`, boucle, structure de données, fichiers | Notebook avec cellules déjà exécutées ; maîtrise à vérifier |
| Extraction → base SQL | `RAG/.../rag/corrige/exercice_01_pipeline_corrige.ipynb` | fonctions, Polars, psycopg, traçabilité ETL | Notebook corrigé disponible ; ne prouve pas une rédaction autonome |
| Chunking et embeddings | `RAG/.../rag/demo_live/demo_chunking_embedding.ipynb` | imports, listes, boucles, objets, NumPy | Notebook documentant le travail RAG |

**Chaîne réelle à savoir raconter :** document ou API → Python extrait/normalise → données validées → PostgreSQL ou Qdrant → requête / modèle → résultat métier. **B5 contient aussi un backend Python indépendant de n8n** ; les deux voies ne sont pas la même implémentation.

## 2. Le modèle mental essentiel : données, variables et types

Une variable est un nom lié à une valeur. Le type de l'objet détermine les opérations permises. Le support de mai présente `str`, `int`, `float`, `bool`, puis `list`, `tuple`, `set`, `dict` et NumPy. Apprends d'abord à reconnaître et manipuler les types intégrés.

```python
nom = "Volleyball"               # str
stock = 0                       # int
prix = 11.99                    # float
disponible = stock > 0          # bool
produit = {"nom": nom, "stock": stock, "prix": prix}   # dict
print(type(produit), disponible)
```

La chaîne `"0"` n'est pas l'entier `0`. `None` indique une absence de valeur et n'est pas équivalent à zéro. En calcul financier, les `float` peuvent avoir de petites erreurs binaires de précision ; pour des montants destinés à la comptabilité, utiliser une stratégie décimale explicite (par ex. `Decimal`) plutôt que d'improviser des égalités de flottants.

### Liste vs dictionnaire vs ensemble

```python
produits = ["Volleyball", "Basketball", "Volleyball"]
produits_uniques = set(produits)               # supprime les doublons, ordre non garanti
stock_par_id = {153: 0, 160: 8}               # clé -> valeur
print(stock_par_id[153])                       # 0
```

Une **liste** conserve l'ordre et les doublons ; un **dictionnaire** permet d'accéder à une valeur par clé ; un **set** déduplique. L'index `produits[0]` récupère le premier élément ; `produits[-1]` le dernier. `produits[1:3]` inclut 1 mais exclut 3.

### Piège : une copie apparente peut partager la même liste

```python
a = [1, 2]
b = a
b.append(3)
assert a == [1, 2, 3]       # même objet
c = a.copy()                # nouvelle liste (copie superficielle)
```

**Contrôle :** sans exécuter, prédire la valeur de `a`, `b` et `c` après `a.append(4)`.

## 3. Conditions, boucles et fonctions : la logique métier avant l'IA

Tu as rencontré une erreur de recommandation : le système affichait Volleyball malgré `stock = 0`. Avant tout LLM, une condition déterministe doit imposer l'interdiction :

```python
def est_recommandable(produit: dict) -> bool:
    stock = produit.get("stock")
    return isinstance(stock, int) and stock > 0

catalogue = [
    {"id": 153, "nom": "Volleyball", "stock": 0},
    {"id": 160, "nom": "Basketball", "stock": 8},
]

for produit in catalogue:
    if est_recommandable(produit):
        print("Disponible :", produit["nom"])
    else:
        print("À exclure :", produit["nom"])
```

**Important :** les identifiants et stocks de cet exemple sont *illustratifs*, et ne constituent pas une nouvelle lecture en direct du catalogue DummyJSON. Le principe se retrouve dans le backend B5 : faire valider les informations produits par le programme, pas par une simple phrase du modèle.

Une fonction reçoit des arguments, exécute une logique et retourne une valeur avec `return`. La distinction **définition** (`def`) / **appel** (`est_recommandable(...)`) est fondamentale. Une fonction courte se teste et se réutilise plus facilement.

### Comprendre les compréhensions de liste

```python
disponibles = [p for p in catalogue if est_recommandable(p)]
```

C'est l'équivalent compact d'une boucle `for` avec `if` et `append`. **Au stade actuel :** sache d'abord écrire la boucle longue ; adopte ensuite la syntaxe compacte.

## 4. Les vrais fichiers du Z4 : `Path`, imports et JSON

Dans le notebook GitHub `01_intro.ipynb`, on voit réellement :

```python
from pathlib import Path
import pymupdf as pypdf
import polars as pl
CORPUS = Path('data/veltis')
```

**`Path`** représente un chemin de fichier. `'data/veltis'` est **relatif au répertoire de travail**, pas nécessairement au dossier contenant le notebook. `import ... as ...` donne un alias pratique : `pl` pour Polars. Ce projet utilise ici **Polars**, pas pandas : il faut savoir distinguer la bibliothèque du cours et celle effectivement présente dans ton notebook.

Mini-labo sans toucher aux données du projet :

```python
from pathlib import Path
p = Path('notes_python.txt')
p.write_text('stock=0\nstock=8\n', encoding='utf-8')
print(p.resolve())
print(p.read_text(encoding='utf-8').splitlines())
```

**À expliquer :** ce qu'affiche `resolve()`, la différence entre texte brut et données structurées, et pourquoi spécifier `encoding='utf-8'`.

JSON correspond à des dictionnaires/listes imbriqués. B5 utilise effectivement `import json` pour communiquer avec des services et mémoriser des structures de données. Exemple de lecture :

```python
import json
message = '{"product_id": 153, "stock": 0}'
data = json.loads(message)        # texte JSON -> dictionnaire Python
assert data['stock'] == 0
texte = json.dumps(data)          # dictionnaire Python -> texte JSON
```

**Distinguer :** `json.loads` (chaîne), `json.load` (fichier), `json.dumps` (chaîne), `json.dump` (fichier).

## 5. Lire une API : `requests`, statut HTTP et validation

Le fichier GitHub `app.py` importe réellement `requests` et utilise `requests.Session()` pour appeler le catalogue, Qdrant et les services de modèles. Exemple **pédagogique**, sans connexion nécessaire :

```python
# Schéma de la démarche (à exécuter uniquement si réseau disponible)
import requests
r = requests.get('https://dummyjson.com/products/153', timeout=10)
r.raise_for_status()              # exception si erreur HTTP 4xx/5xx
data = r.json()                    # JSON de réponse -> objet Python
print(data.get('title'), data.get('stock'))
```

Ne suppose jamais qu'une réponse réseau est bonne simplement parce qu'un programme n'a pas affiché d'erreur. Vérifier : délai (`timeout`), code de réponse, clés attendues, type du stock et provenance des valeurs. La recommandation s'appuie sur une **lecture de stock actuelle** ; une ancienne valeur indexée peut être périmée.

## 6. NumPy : pourquoi vectoriser ?

Le support de mai introduit `numpy.ndarray`, les types homogènes (`dtype`), la forme (`shape`), le découpage, les masques booléens, les agrégations et le broadcasting. NumPy permet de faire les calculs sur tout un ensemble de valeurs sans écrire une boucle Python élément par élément.

```python
import numpy as np
stock = np.array([0, 8, 4, 0])
prix = np.array([11.99, 14.99, 29.00, 9.50])
masque = stock > 0
print(masque)                # [False True True False]
print(prix[masque])          # [14.99 29.  ]
print(stock.sum())           # 12
print(stock.shape)           # (4,)
```

**Masque booléen** : tableau de `True` et `False` qui sélectionne les valeurs. **`shape`** : dimensions ; **`dtype`** : type interne ; **`axis`** : direction d'une agrégation (important en tableau 2D). Le notebook de chunking importe NumPy ; cela atteste son utilisation dans un exercice, **pas une maîtrise indépendante de la vectorisation**.

**Test mental :** pour une matrice de 3 lignes × 2 colonnes, `sum(axis=0)` renvoie combien de nombres ? Réponse : deux, un par colonne.

## 7. pandas et Polars : passer d'une liste à un tableau

Le support de mai couvre **pandas** (DataFrame, sélection, filtres, valeurs manquantes, jointures, `groupby`, CSV). Ton pipeline ETL d'octobre utilise **Polars** dans le notebook corrigé. Les idées métier restent les mêmes : une table, des lignes, des colonnes, des règles de transformation.

```python
import pandas as pd

df = pd.DataFrame({
    'produit': ['Volleyball', 'Basketball', 'Tennis Racket'],
    'stock': [0, 8, 3],
    'prix': [11.99, 14.99, 65.00],
})

disponibles = df.loc[df['stock'] > 0, ['produit', 'prix']]
print(disponibles)
```

Ce fragment illustre pandas et n'est **pas** une citation de ton notebook RAG. Dans Polars, on écrirait par exemple :

```python
import polars as pl
pl_df = pl.DataFrame({'produit': ['Volleyball', 'Basketball'], 'stock': [0, 8]})
print(pl_df.filter(pl.col('stock') > 0))
```

**Réflexes de qualité :** inspecter types et lignes ; contrôler les `NULL`/`NaN` ; vérifier doublons ; définir la clé métier ; confirmer les unités et les devises. `drop_duplicates()` peut détruire des données légitimes si la clé est mal définie.

## 8. Machine learning du support : comprendre, sans disperser le parcours

Le support aborde ensuite scikit-learn : découpage entraînement/test, prétraitements, estimateurs, classification, régression, métriques, validation croisée, surapprentissage, clustering, PCA, arbres et ensembles. Pour l'instant, cet ensemble est un **niveau de lecture**, pas une nouvelle piste de spécialisation prioritaire.

**Schéma général :** définir une question → préparer des colonnes/features et une cible → séparer les données (en évitant les fuites) → établir une baseline → entraîner → évaluer sur données tenues à l'écart → expliquer les limites.

| Tâche | Exemple métier | Mesure de départ |
|---|---|---|
| Régression | prévoir une quantité de production | MAE / erreur absolue moyenne |
| Classification | repérer un document mal classé | précision, rappel, matrice de confusion |
| Clustering | regrouper des profils de documents | qualité/interprétation des groupes, pas seulement un score |

**Point critique :** un RAG avec embeddings et Qdrant n'est pas automatiquement un modèle supervisé entraîné avec scikit-learn. Dans B5 et dans le pipeline Docling, tu as surtout mis en œuvre **ingestion, recherche et intégration de modèles déjà disponibles**.

## 9. Test de compréhension : retracer B5 sans aide

Repère le fichier réel **`app.py`** sur GitHub. Cherche les éléments suivants et explique-les en une phrase chacun : `import json`, `os.getenv`, `def`, `try/except` ou la gestion des erreurs, `requests.Session()`, `return`, les listes et les dictionnaires.

### Trois blocs de 45 minutes (sans assistance IA pendant la résolution)

**Bloc A — Fondations.** Dans un script vierge, crée trois produits sous forme de liste de dictionnaires. Écris une fonction qui sélectionne les produits disponibles et renvoie leurs noms. Ajoute trois assertions : tous indisponibles, mélange, stock manquant.

**Bloc B — Données tabulaires.** Convertis les mêmes produits en `pandas.DataFrame` **ou** `polars.DataFrame` (choisis une seule bibliothèque par exercice). Filtre le stock positif, trie par prix et calcule le nombre de produits éligibles. Compare le résultat avec la fonction du bloc A.

**Bloc C — Source de données.** Charge un petit fichier JSON créé par toi, vérifie que toutes les lignes ont un ID, repère les doublons, enregistre un rapport texte comprenant : nombre de lignes, nombre disponibles, anomalies. Pas de Qdrant ni de Nemotron requis pour ce test.

### Échelle d'évaluation des compétences

- **Vu** : tu reconnais `for`, `dict`, `DataFrame`, API et peux en expliquer l'objectif.
- **Avec assistance** : tu modifies du code existant en suivant un exemple ou une réponse de l'IA.
- **Autonome** : tu pars d'un fichier vide, réalises les blocs A/B/C et expliques les erreurs rencontrées.
- **Prouvé** : tu conserves le code, les assertions et une courte explication des résultats dans GitHub, sans données privées.

### Autotest — réponses à formuler sur papier

1. Pourquoi `stock = '0'` ne doit-il pas être comparé directement à l'entier `0` ?
2. Différence entre `dict.get('stock')` et `dict['stock']` si la clé manque ?
3. Qu'affiche `[x for x in [1, 2, 3] if x > 1]` ?
4. Pourquoi une requête HTTP peut réussir sur le réseau mais produire une mauvaise recommandation ?
5. Quelles différences entre `np.array`, `pd.DataFrame` et `pl.DataFrame` ?
6. Quelle preuve montrerais-tu qu'un contrôle de stock fonctionne sans intervention de l'IA ?

## 10. Références vérifiées et suite

**Support collègue :** `2026 Cours.zip` → `2026-05 - Python pour la data science.md` ; progression du support : environnement, types, conditions/boucles, collections, NumPy, pandas, EDA, scikit-learn. Complément des notions de chaînes et exceptions : `2026-08-03_10 - Bases Python et visualisation.md`.

**GitHub — fichiers consultés :**

- https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py
- https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py
- https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb
- https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb
- https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb

**À garder distinct :** les exemples simplifiés de ce document sont construits pour l'apprentissage. Ils ne doivent pas être présentés comme des extraits fidèles de tes scripts lorsqu'ils ne le sont pas. La présence d'une solution corrigée ne démontre pas une maîtrise personnelle.

**Passage au prochain cours :** restituer le parcours des données de B5 en 5 étapes, puis démontrer sans assistance la fonction de contrôle du stock et un test automatique réussi. Le prochain support de la série chronologique traitera de PostgreSQL : modélisation et SQL déclaratif, avant la programmation SQL procédurale.
