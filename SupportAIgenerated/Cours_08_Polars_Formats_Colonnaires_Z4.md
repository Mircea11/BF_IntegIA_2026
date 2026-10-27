# Cours personnel 08 — Polars et formats colonnaires

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Support principal :** `2026-08-24 - Polars et formats colonnaires.md` dans `2026 Cours.zip` (notes de cours de Romain Wauman, 24–25 août et 1er septembre 2026 ; extraits du dépôt pédagogique `exo_polars` et du support *L’écosystème des DataFrames en Python*).  
**Références vérifiées :** dépôt GitHub `Mircea11/BF_IntegIA_2026`, branche `main`, consulté le 26 octobre 2026.  
**Temps conseillé :** lecture 75 à 90 minutes ; trois blocs de 45 minutes ; autotest 15 minutes.  
**Prérequis :** cours 02 (Python), cours 03 (SQL), cours 05 (visualisation).  
**But professionnel :** concevoir un traitement de données reproductible, depuis un fichier source jusqu’à un résultat analysable et contrôlé.

> **Niveau de preuve.** La présence de `polars` dans un notebook et de `pl.read_database()` dans un corrigé confirme une exposition à l’outil, pas son usage autonome. Les exercices ci-dessous sont à faire d’abord sans IA. Les exemples de taxi, NYPD, Delta et Iceberg viennent du support de ton collègue : ils ne sont pas présentés comme des réalisations personnelles.

## 1. Pourquoi ce cours compte dans ton parcours

Tu construis des chaînes où les informations viennent de fichiers, d’API, de documents ou d’une base, puis sont transformées avant de devenir un rapport, un indicateur ou un contexte pour une IA. Polars s’insère dans la **transformation et le contrôle des données tabulaires**.

| Étape | Dans tes projets | Outil typique | Question de contrôle |
|---|---|---|---|
| Entrée | CSV des ventes A1 ; documents du RAG ; catalogue B5 | `read_csv`, `scan_csv`, Docling, HTTP | D’où viennent les données ? |
| Structuration | Données par colonnes et types | Polars / SQL | Quelles colonnes, quels types, quelles valeurs manquantes ? |
| Transformation | Filtre, nettoyage, regroupement | `filter`, `with_columns`, `group_by` | Le résultat suit-il la règle métier ? |
| Persistance | Table relationnelle ou fichier analytique | PostgreSQL, Parquet | Peut-on relire et reproduire ? |
| Exploitation | Reporting, dashboard, décision | Graphiques, SQL, BI | Le chiffre est-il vérifié et explicable ? |

**Frontière importante :** Polars ne remplace pas Docling pour extraire le contenu d’un PDF, PostgreSQL pour stocker des transactions, ni Qdrant pour rechercher des vecteurs. Ces outils peuvent appartenir à la même architecture sans être interchangeables.

## 2. NumPy, pandas, Polars : que choisir ?

Le support commence par une distinction de forme des données : liste Python pour quelques valeurs ; **NumPy** pour les tableaux numériques homogènes ; **pandas/Polars** pour les tableaux où les colonnes ont des types différents (produit texte, quantité entier, montant numérique).

| Outil | Structure dominante | Usage conseillé ici | Réserve |
|---|---|---|---|
| Liste/dictionnaire Python | Objets flexibles | Quelques produits, payload JSON | Boucles et conversions coûteuses sur gros volumes |
| NumPy | Matrice de valeurs typées, homogènes | Embeddings, calculs numériques | Peu pratique pour données métier hétérogènes |
| pandas | DataFrame tabulaire | Exploration et intégration avec des outils courants | Peut mobiliser beaucoup de mémoire |
| Polars | DataFrame typé, moteur d’expressions | Nettoyage, agréger, joindre, exporter ; mode lazy | Nécessite de maîtriser ses expressions et le schéma |

**Vecteur numérique ≠ embedding.** « Vectoriser » dans Polars signifie appliquer une opération à une colonne entière. Dans BGE-M3, produire un embedding signifie convertir un texte en représentation numérique pour une recherche sémantique. Même mot, finalités différentes.

### Mini-rappel NumPy du 1er septembre

```python
import numpy as np

valeurs = np.array([10, 20, 30], dtype=np.int32)
print(valeurs * 2)               # [20 40 60]
print(np.linspace(0, 1, 5))     # cinq points, quatre intervalles
print(np.arange(1, 5))          # 1, 2, 3, 4 : fin exclue
```

Un `Int32` représente **32 bits, donc 4 octets** par valeur brute ; ce n’est pas « 32 octets ». Le *broadcasting* permet aussi d’appliquer un vecteur à chaque ligne d’une matrice si les dimensions sont compatibles.

## 3. Comprendre le stockage : lignes, colonnes, Arrow et Parquet

Une table de ventes pourrait être représentée ainsi :

| produit | quantité | revenu |
|---|---:|---:|
| Cat Food | 37 | 267,30 |
| Samsung Galaxy S10 | 31 | 18 205,47 |
| Generic Motorcycle | 28 | 87 485,59 |

En **stockage orienté ligne**, les valeurs d’un enregistrement sont regroupées : pratique pour lire ou modifier une commande complète. En **stockage orienté colonne**, toutes les quantités sont proches, puis tous les revenus : pratique pour calculer la somme des ventes sans lire le détail des descriptions de produit.

- **Arrow :** format colonnaire en mémoire et interface d’échange entre moteurs. Il peut limiter les copies lorsque les représentations sont compatibles ; « zéro copie » n’est pas garanti pour toute conversion.
- **Parquet :** fichier colonnaire sur disque, compressé et décrit par des métadonnées. Ce n’est pas une base transactionnelle.
- **Polars :** moteur qui interroge et transforme les colonnes ; il peut lire CSV, JSON, Parquet et, dans certains cas, des résultats SQL.
- **PostgreSQL :** base adaptée aux écritures et consultations transactionnelles, à la cohérence et aux relations. Ton B5 conserve notamment les messages des sessions dans PostgreSQL.

**À retenir :** CSV n’est pas, à lui seul, un stockage analytique colonnaire typé. Il est textuel et requiert une interprétation des types à la lecture. Parquet porte son schéma et peut éviter de lire des colonnes inutiles.

### Pourquoi les performances peuvent augmenter

Le support explique trois leviers : **colonnes homogènes**, **opérations vectorisées**, **parallélisme** sur plusieurs cœurs, parfois avec des instructions SIMD. Un traitement *lazy* peut aussi supprimer du travail inutile avant l’exécution. Aucun facteur de vitesse universel ne peut être garanti ; il dépend des volumes, types, requêtes et machines.

## 4. Eager ou lazy : la différence décisive

**Eager** : on lit et on calcule immédiatement. **Lazy** : on construit d’abord un plan de calcul, puis `collect()` l’exécute.

```python
import polars as pl

# Eager : le CSV est lu maintenant.
df = pl.read_csv("N8N/data/top5_produits.csv")
print(df.shape)

# Lazy : plan de traitement, pas encore de résultat.
plan = (
    pl.scan_csv("N8N/data/top5_produits.csv")
    .filter(pl.col("quantity") >= 28)
    .select("product", "quantity", "revenue_eur")
    .sort("quantity", descending=True)
)

print(plan.collect_schema())  # inspecter noms et types
print(plan.explain())         # inspecter le plan optimisé
resultat = plan.collect()     # exécuter le calcul
print(resultat)
```

**Pourquoi c’est utile :** le moteur peut effectuer un *predicate pushdown* (filtrer tôt) et un *projection pushdown* (lire seulement les colonnes nécessaires). Dans l’exemple minuscule de cinq lignes, le bénéfice est surtout pédagogique, pas une optimisation mesurable.

**Piège :** `pl.read_csv(...).lazy()` transforme un DataFrame déjà chargé en LazyFrame : cela ne récupère pas le temps ni la mémoire de lecture du fichier. Préférer `pl.scan_csv(...)` pour construire le pipeline dès l’entrée.

## 5. Cinq opérations Polars à écrire sans assistance

Le support du collègue introduit `select`, `filter`, `with_columns`, `group_by`, `join`, ainsi que `over`, les dates et le SQL sur LazyFrame. Nous les appliquons aux ventes du projet A1.

### 5.1 Charger et contrôler le schéma

```python
import polars as pl

ventes = pl.scan_csv("N8N/data/top5_produits.csv")
print(ventes.collect_schema())
print(ventes.select(pl.len().alias("nombre_lignes")).collect())
```

Résultat **attendu pour la version vérifiée sur GitHub** : cinq lignes, trois colonnes (`product`, `quantity`, `revenue_eur`). Les types numériques sont inférés à partir du CSV : vérifie-les sur ta copie locale avant de poursuivre.

### 5.2 Sélectionner, filtrer, trier

```python
selection = (
    ventes
    .filter((pl.col("quantity") >= 28) & (pl.col("revenue_eur") > 1000))
    .select("product", "quantity", "revenue_eur")
    .sort("revenue_eur", descending=True)
)
print(selection.collect())
```

L’opérateur `&` signifie ET ; `|` signifie OU ; `~` inverse une condition. **Mettre des parenthèses autour des comparaisons** pour éviter les erreurs de priorité des opérateurs.

### 5.3 Créer une colonne calculée

```python
avec_indicateur = ventes.with_columns(
    (pl.col("revenue_eur") / pl.col("quantity"))
      .round(2)
      .alias("revenu_par_unite")
)
print(avec_indicateur.collect())
```

Ici, `revenu_par_unite` est **un indicateur dérivé** du rapport, pas nécessairement le prix catalogue unitaire. Il n’inclut aucune preuve sur les remises, taxes, retours ou devises des transactions d’origine.

### 5.4 Agréger et contrôler les totaux

```python
controle = ventes.select(
    pl.len().alias("lignes"),
    pl.col("quantity").sum().alias("quantites_total"),
    pl.col("revenue_eur").sum().round(2).alias("revenus_total_eur"),
)
print(controle.collect())
```

**Attendu pour ce fichier :** `lignes = 5`, `quantites_total = 150`, `revenus_total_eur = 108927.66`. Ce sont des **totaux des cinq produits du fichier**, pas les ventes totales de l’entreprise. Pour une réconciliation financière, les flottants de lecture CSV doivent être contrôlés ; les calculs monétaires sensibles requièrent une politique de précision, par exemple `Decimal`.

### 5.5 Joindre une table de référence

Une jointure enrichit les faits avec une dimension, comme en SQL.

```python
familles = pl.DataFrame({
    "product": ["Cat Food", "Samsung Galaxy S10", "Generic Motorcycle",
                "Plant Pot", "Apple Airpods"],
    "family": ["Pets", "Phones", "Vehicles", "Home", "Audio"],
}).lazy()

enrichi = ventes.join(familles, on="product", how="left")
print(enrichi.select("product", "family", "quantity").collect())
```

La table `familles` est **une construction pédagogique**, pas une classification officielle de ton catalogue. Après une jointure, il faut vérifier l’unicité de la clé du référentiel : des doublons côté dimension peuvent multiplier les lignes et fausser un total.

## 6. Fenêtres et séries temporelles : l’étape suivante

Le support aborde `over()` comme l’équivalent de `PARTITION BY` en SQL, et différencie deux calculs temporels :

- `rolling` : fenêtre mobile autour des observations ; nécessite un ordre temporel correct ;
- `group_by_dynamic` : regroupe les événements en plages fixes (heures, jours, semaines) ;
- `.dt.weekday()` : extrait un jour de semaine ; `.dt.strftime(...)` formate une date.

Exemple autonome à comprendre, **sans rapport avec ton fichier A1**, qui ne possède pas de colonne de date :

```python
from datetime import date
import polars as pl

j = pl.DataFrame({
    "date": [date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)],
    "famille": ["A", "A", "B"],
    "valeur": [10, 20, 15],
})
print(j.with_columns(
    pl.col("valeur").sum().over("famille").alias("total_famille")
))
```

Tu reconnais ici la logique des indicateurs de production : somme par famille, suivi d’une période, comparaison de séries temporelles. À ce stade, la priorité est de comprendre les opérations de base ; le temporel avancé reste un exercice complémentaire.

## 7. CSV vers Parquet : une petite chaîne ETL reproductible

**ETL = Extraire, Transformer, Charger.** Pour un exercice local, le « chargement » peut être un fichier Parquet qui sera lu par un autre programme.

```python
from pathlib import Path
import polars as pl

source = Path("N8N/data/top5_produits.csv")
cible = Path("sorties/top5_produits_controles.parquet")
cible.parent.mkdir(parents=True, exist_ok=True)

plan = (
    pl.scan_csv(source)
    .filter(pl.col("quantity") > 0)
    .select("product", "quantity", "revenue_eur")
)

# Dataset minuscule : collect() est acceptable pour l'exercice.
resultat = plan.collect()
resultat.write_parquet(cible)

# Contrôle aller-retour : schéma, nombre de lignes, total.
relecture = pl.scan_parquet(cible)
print(relecture.collect_schema())
print(relecture.select(
    pl.len().alias("lignes"),
    pl.col("quantity").sum().alias("quantites")
).collect())
```

**Sur un très gros volume**, on préférera étudier une écriture en streaming (`sink_parquet`), plutôt que de charger tout le résultat avec `collect()`. Les capacités exactes dépendent de la version de Polars installée sur ton Z4.

### Pourquoi Parquet est plus efficace pour l’analyse

Son organisation est : **fichier → row groups → column chunks → pages**. Le *footer* contient notamment le schéma et des statistiques qui peuvent permettre de sauter des blocs ne correspondant pas à un filtre. Deux techniques centrales :

- **Projection pushdown** : seules les colonnes utiles sont lues.
- **Predicate pushdown / pruning** : des filtres permettent de ne pas lire certains blocs.

Ces optimisations ne garantissent pas que chaque filtre supprime une lecture : si tous les blocs couvrent la même plage de valeurs, le *pruning* peut être faible. Évite donc `collect()` ou `select('*')` avant d’avoir défini ton besoin.

## 8. Delta Lake, Iceberg et volumes plus grands que la RAM

Le support complète Polars par l’architecture *lakehouse*. Le point essentiel : **Parquet est un format de fichier ; Delta Lake et Apache Iceberg sont des formats de table reposant notamment sur des fichiers Parquet et des métadonnées**.

| Élément | Parquet | Delta Lake / Iceberg |
|---|---|---|
| Schéma et colonnes | Oui, par fichier | Oui, au niveau de la table |
| Transactions concurrentes | Non, pas à lui seul | Prévues par le format de table |
| Historique des versions | Non, pas à lui seul | Fonctionnalité centrale |
| Évolution contrôlée du schéma | Manuelle au niveau des fichiers | Gouvernée au niveau table |
| Usage pour toi maintenant | Oui : exercice CSV → Parquet | À connaître, pas à déployer ce mois-ci |

**Pruning à quatre niveaux**, selon le support : partition du répertoire, statistiques de row groups, index de pages lorsqu’ils existent et filtre final sur les valeurs décodées. Il rappelle aussi les dangers : milliers de petits fichiers, schémas incompatibles, partitions à trop forte cardinalité.

Le pipeline pédagogique **TLC** (209 fichiers mensuels, d’après le support) illustre l’inventaire, le manifeste, les téléchargements repris, la réconciliation des schémas et l’écriture partitionnée. **Ce pipeline n’est pas attesté dans ton GitHub consulté** ; il reste une référence d’architecture, pas un acquis personnel.

## 9. Ce que tes fichiers GitHub prouvent réellement

| Référence consultée | Constat observable | Niveau à retenir |
|---|---|---|
| [RAG — `demo/01_intro.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb) | Import de `polars as pl` pendant l’exploration de documents | Outil rencontré ; autonomie non démontrée |
| [RAG — `corrige/exercice_01_pipeline_corrige.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb) | Usage de `pl.read_database(...)` sur des requêtes de contrôle d’ETL | Exemple de lecture SQL → DataFrame ; corrigé, pas preuve d’auteur indépendant |
| [n8n — `data/top5_produits.csv`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/top5_produits.csv) | Trois colonnes, cinq produits ; quantités et montants observables | Jeu réel de sortie A1 utilisable pour s’exercer |
| [n8n — `data/rapport_usage_modele.json`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/rapport_usage_modele.json) | Traçage du modèle, temps et tokens | Source complémentaire de métadonnées, pas un DataFrame Polars démontré |

**Chaîne professionnelle à retenir :** source identifiée → schéma contrôlé → transformation explicable → validation numérique → export reproductible → présentation. C’est la logique transférable à tes données de production, supply chain et intelligence de marché.

## 10. Programme pratique sur journée libre

### Bloc A — 45 minutes : reconstruire un pipeline simple

**Sans IA.** Dans `~/formation`, crée un fichier séparé `exercice_polars_08.py` (ne modifie pas B5). Utilise le CSV de cinq produits déjà dans `N8N/data/`.

1. Affiche le nombre de lignes et les types des trois colonnes.
2. Conserve uniquement les produits dont `quantity >= 28`.
3. Trie par `revenue_eur` décroissant.
4. Affiche le nombre de produits retenus.
5. Explique à voix haute la différence entre `scan_csv`, `read_csv` et `collect`.

**Preuve à conserver :** code + sortie terminal, sans copie de corrigé.

### Bloc B — 45 minutes : contrôle des totaux et qualité

1. Produis les KPI : nombre de lignes, somme des quantités, somme des revenus.
2. Vérifie séparément l’addition à partir du CSV d’origine.
3. Simule une ligne avec une quantité manquante : détecte-la, décide de la règle métier, puis affiche le nombre de lignes rejetées.
4. Exporte les lignes valides en Parquet et relis-les.
5. Note les limites : arrondis, couverture partielle du top 5, absence de périodes et de prix de vente individuels.

**Attendu avant modification du jeu :** 5 lignes, 150 unités et 108 927,66 pour le revenu des cinq lignes. Une autre copie locale peut produire d’autres chiffres ; dans ce cas, conserver les valeurs effectivement observées.

### Bloc C — 45 minutes : mini-rapport professionnel

1. Prépare une table `product | quantity | revenue_eur | revenue_per_unit`.
2. Identifie les deux produits de plus fort revenu (ne confonds pas revenu et quantité).
3. Écris cinq lignes de commentaire en distinguant **observation**, **interprétation** et **limite**.
4. Fais une jointure avec une table de familles inventée et vérifie que le nombre de lignes reste égal à cinq.
5. Explique ce qui changerait si tu avais 20 millions de lignes et 24 fichiers Parquet mensuels.

**Livrable facultatif :** une capture du tableau de résultats, plus un court README avec la source, les colonnes, les règles de filtre, les contrôles et les limites. Pas de nouvelle branche ni de refonte de projet pendant cet exercice.

## 11. Autotest : dix questions

Réponds sans relire le cours, puis vérifie le corrigé.

1. Quelle différence entre `pl.read_csv` et `pl.scan_csv` ?
2. Quelle ligne lance le calcul d’un `LazyFrame` ?
3. Pourquoi `pl.read_csv(...).lazy()` ne donne-t-il pas tous les avantages d’un scan ?
4. Que fait `.filter((pl.col("quantity") > 0) & (pl.col("revenue_eur") > 100))` ?
5. Quel risque métier présente une jointure avec une table de référence contenant des clés dupliquées ?
6. Quelle différence entre une colonne Arrow et un fichier Parquet ?
7. À quoi servent predicate et projection pushdown ?
8. Pourquoi ne pas annoncer que les cinq lignes de `top5_produits.csv` représentent toutes les ventes ?
9. Qu’ajoutent Delta Lake et Iceberg au-delà de Parquet ?
10. Pourquoi l’import `import polars as pl` dans ton notebook ne suffit-il pas pour déclarer la compétence « maîtrisée » ?

### Corrigé condensé

1. Lecture immédiate contre plan de lecture différée.
2. `collect()` ; certaines sorties `sink_*` exécutent directement un plan vers un fichier.
3. Le fichier a déjà été lu ; l’optimiseur ne peut plus repousser le filtre dans cette lecture.
4. Retient les lignes satisfaisant les **deux** conditions.
5. La jointure peut démultiplier les faits et les sommes.
6. Arrow représente des colonnes en mémoire ; Parquet stocke un fichier analytique compressé sur disque.
7. Lire moins de lignes/blocs et moins de colonnes lorsque la structure et les statistiques le permettent.
8. C’est un extrait « top 5 », sans preuve sur la période, la population totale ni les autres produits.
9. Gestion transactionnelle, versions, modifications et métadonnées de table.
10. Un import est un indice d’exposition ; l’autonomie se prouve par une réalisation indépendante, testée et expliquée.

## 12. Tableau de compétence à renseigner après l’exercice

| Compétence | État établi aujourd’hui | Critère pour passer à « indépendant » |
|---|---|---|
| Lire du code Polars | Exposition vérifiée | Expliquer un filtre et une agrégation sans aide |
| Écrire `scan_csv → filter → select → collect` | Non démontré par les preuves consultées | Script personnel exécuté et résultat attendu |
| Détecter des erreurs de schéma ou données | À tester | Contrôle de types et valeurs manquantes, justification écrite |
| Exporter et relire Parquet | À tester | Fichier produit, contrôles avant/après égaux |
| Interpréter un tableau métier | À tester | Conclusion avec source, périmètre, unités et limites |

**Décision de progression :** une fois les blocs A et B réussis sans assistance, passe au module suivant. Si un bloc échoue, corrige uniquement la notion défaillante ; ne recommence pas le cours entier.

## Sources et vérifications

**Source primaire de la formation :** `2026 Cours.zip` → `2026-08-24 - Polars et formats colonnaires.md`, y compris ses sections « 24/08 », « 25/08 », « 01/09 », syntaxe issue de `exo_polars`, exercices NYPD, pipeline TLC et compléments sur Parquet/Delta/Iceberg. Ces exercices pédagogiques sont décrits dans le support ; je n’ai pas inspecté le dépôt externe `exo_polars`.

**Sources personnelles vérifiées sur GitHub :**

- `N8N/data/top5_produits.csv` : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/top5_produits.csv
- `RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb` : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb
- `RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb` : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb
- `N8N/data/rapport_usage_modele.json` : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/rapport_usage_modele.json

**Vérification documentaire externe des opérations Polars :**

- Guide officiel sur l’API lazy : https://docs.pola.rs/user-guide/concepts/lazy-api/
- Référence officielle des entrées/sorties : https://docs.pola.rs/api/python/stable/reference/io.html
- Guide sur les optimisations : https://docs.pola.rs/user-guide/lazy/optimizations/

**Limite de validation :** les extraits Polars ont été recoupés avec la documentation officielle, mais **n’ont pas été exécutés sur ton Z4**. Il faut donc vérifier la version installée et les sorties locales. Aucun résultat d’exercice personnel n’a été inventé.
