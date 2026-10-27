# Cours personnel 05 — Python et visualisation : des données à une décision

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Source principale :** `2026-08-03_10 - Bases Python et visualisation.md`, dans `2026 Cours.zip` (notes de cours de Cédric Van Osselaer, 3–10 août 2026).  
**Continuité :** cours 02 (types, conditions, fonctions, fichiers) → **cours 05 (précision du code + matplotlib)**.  
**Durée :** lecture de 60–80 min + trois blocs de 45 min.  
**Environnement :** Ubuntu HP Z4, dépôt `Mircea11/BF_IntegIA_2026` ; exemples sans modification des données de production.

> **Résultat attendu :** savoir lire des résultats de traitement, vérifier leurs types, choisir un graphique adapté, écrire un graphique avec `matplotlib` et expliquer les décisions prises. Ne pas confondre « module étudié » et « opération réalisée seul ».

## 1. D'où vient ce cours, et ce qu'il ajoute

Ton collègue indique que le module du **3 au 10 août 2026** combine une reprise des bases Python (affichage, f-strings, chaînes, collections, erreurs) et un bloc conséquent sur **matplotlib**. Il ajoute ensuite des précisions tirées du support « Python – Les bases » (121 diapositives). Ce document conserve cette structure ; il **ne remplace pas** le cours 02, qui traite déjà Python pour la data science.

| Sujet | Dans les notes du collègue | Priorité ici |
|---|---|---|
| `print`, `type`, `display`, f-strings | Reprise des bases | A — maîtriser sans aide |
| `split`, `join`, conversions, `None` | Reprise et précisions | A — maîtriser sans aide |
| Listes, dictionnaires, `sort`, `get`, slicing | Complément au support « Les bases » | A — tester les pièges |
| Choix `plot`, `bar`, `hist`, `scatter`, `pie` | Module matplotlib | A — savoir choisir |
| Titres, axes, légendes, formatage | Module matplotlib | A — produire un résultat propre |
| `**kwargs`, `subplot`, style objet `fig, ax` | Module matplotlib | B — écrire un cas simple |
| `imshow`, image RGB/RGBA, `cmap` | Module matplotlib | B — comprendre, sans priorité métier |
| `eval`, `is`, `match`, `map`, exceptions | Nuances / compléments au support | B — éviter les contresens |

**État observé :** les fichiers GitHub vérifiés montrent du Python, des APIs, des données et des notebooks. Ils **ne constituent pas une preuve** que tu as déjà réalisé de façon autonome une visualisation matplotlib reproductible. C'est précisément ce que ce cours cherche à établir.

## 2. Le cas professionnel : ton vrai fichier de ventes

**Fichier vérifié sur GitHub :** [N8N/data/top5_produits.csv](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/top5_produits.csv). Il contient les colonnes `product`, `quantity`, `revenue_eur`. Voici **les valeurs du fichier versionné**, et non un état en direct des ventes :

| Produit | Quantité | Revenu (`revenue_eur`) |
|---|---:|---:|
| Cat Food | 37 | 267,30 € |
| Samsung Galaxy S10 | 31 | 18 205,47 € |
| Generic Motorcycle | 28 | 87 485,59 € |
| Plant Pot | 27 | 335,05 € |
| Apple Airpods | 27 | 2 634,25 € |

**Question métier :** quels produits sont les plus vendus **en nombre d'unités** ? Un graphique en barres convient, car les produits sont des catégories distinctes. Une autre question (« lesquels génèrent le plus de revenu ? ») nécessite un **autre graphique** et une échelle différente. La moto produit beaucoup plus de revenu que les autres références ; réunir quantités et euros sur un seul axe serait trompeur.

Ton rapport [N8N/data/rapport_usage_modele.json](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/rapport_usage_modele.json) distingue aussi chiffres calculés, consommation du modèle et mesures non disponibles : c'est la même discipline à appliquer aux graphiques. Il signale explicitement que les **5,393 secondes** mesurées comprennent l'orchestration n8n et ne représentent **pas** le temps d'inférence GPU pur.

**Provenance :** les données ci-dessus viennent des fichiers GitHub déjà enregistrés. Elles ne prouvent ni leur exhaustivité commerciale ni la fraîcheur des ventes.

## 3. Python de base : produire une information fiable

### 3.1 `print`, `type`, f-strings

```python
produit = "Apple Airpods"
quantite = 27
revenu = 2634.25

print("Produit", produit, sep=" : ")
print(type(quantite))             # <class 'int'>
print(f"{produit} — {quantite} unités — {revenu:.2f} €")
print(f"{quantite=}")            # quantite=27 (utile pour le diagnostic)
```

- `sep` est le séparateur entre **plusieurs arguments** de `print` ; `end` définit la fin de l'affichage.
- `type()` contrôle le type réel. `"27"` est une chaîne, pas un entier.
- `f"{revenu:.2f}"` formate à deux décimales **sans modifier la valeur stockée**.
- Dans Jupyter, `display()` produit un affichage enrichi ; dans un script, `print()` reste le contrôle de base.

### 3.2 Chaînes : `split` et `join`

```python
"A  B".split()       # ['A', 'B'] : espaces consécutifs ignorés
"A  B".split(" ")    # ['A', '', 'B'] : séparation littérale
" / ".join(["A", "B"])  # 'A / B'
```

**À retenir :** n'utilise pas `split(",")` pour parser un CSV professionnel : les champs entre guillemets peuvent contenir des virgules. Utilise le module `csv` de Python.

### 3.3 Conversion, `None` et validation

```python
def convertir_quantite(texte):
    if texte is None or texte.strip() == "":
        raise ValueError("Quantité absente")
    valeur = int(texte)
    if valeur < 0:
        raise ValueError("Quantité négative")
    return valeur

assert convertir_quantite("27") == 27
```

`None` = absence de valeur ; `0` = valeur numérique valide. `is None` teste l'absence ; `==` compare des valeurs. Le support rappelle que `input()` renvoie toujours du texte. `eval()` **n'est pas** une fonction de conversion sûre pour du texte non fiable : elle évalue du code Python.

### 3.4 Listes et dictionnaires : trois pièges fréquents

```python
produits = ["A", "B", "A"]
uniques = set(produits)                 # doublons retirés, ordre non garanti

lignes = [{"produit": "A", "qte": 3}, {"produit": "B", "qte": 5}]
print(lignes[0].get("qte", 0))           # 3

quantites = [5, 2, 3]
quantites.sort()                       # modifie la liste ; renvoie None
copie_triee = sorted(quantites)         # renvoie une nouvelle liste
```

Autres pièges documentés par ton collègue : `l[:]` fait une **copie superficielle** ; une fonction avec `liste=[]` comme valeur par défaut peut partager cette même liste entre appels ; `pop()` sur un `set` retire un élément arbitraire (pas un tirage aléatoire). Sur Python actuel, les dictionnaires conservent l'ordre d'insertion.

### 3.5 Exceptions utiles quand les données sont imparfaites

```python
try:
    quantite = convertir_quantite("abc")
except ValueError as exc:
    print(f"Entrée rejetée : {exc}")
```

L'objectif n'est pas de « masquer » une erreur, mais d'expliquer la donnée rejetée. Évite `except:` sans précision. Le support recommande `with open(...)` pour fermer les fichiers même lorsqu'une erreur intervient.

## 4. Choisir le bon graphique avant d'écrire le code

| Question | Graphique matplotlib | Pourquoi |
|---|---|---|
| Comment évolue une demande semaine après semaine ? | `plot(x, y)` | Série temporelle ordonnée |
| Quel produit possède la plus grande quantité ? | `bar(x, height)` | Comparaison entre catégories |
| Comment se répartissent 1 000 valeurs individuelles ? | `hist(x, bins=...)` | Distribution numérique, observations brutes |
| Prix et volume semblent-ils liés ? | `scatter(x, y)` | Relation entre deux variables numériques |
| Quelle part représente chaque catégorie d'un total ? | `pie(x, labels=...)` | À limiter à peu de catégories clairement comparables |

**Erreur classique à savoir détecter :** `top5_produits.csv` contient **cinq quantités agrégées par produit**, pas les 150 observations individuelles de ventes. Faire `hist([37, 31, 28, 27, 27])` mesurerait la **distribution des cinq totaux**, et non une distribution des ventes ; pour comparer les cinq produits, il faut `bar`.

**Bonne pratique métier :** unité sur l'axe, titre informatif, source, périmètre (top 5), et absence de promesse causale. C'est aussi vrai pour un futur dashboard de prévision de production ou de supply chain.

## 5. Premier graphique reproductible avec les vrais chiffres du dépôt

Préparation sur le Z4 (dossier contenant le dépôt) :

```bash
cd ~/formation
python3 -c "import matplotlib; print(matplotlib.__version__)"
```

Si la bibliothèque manque, l'installer **dans un environnement virtuel existant** ou adapté au projet ; ne pas modifier à l'aveugle l'environnement système. Le script ci-dessous suppose qu'il est exécuté depuis `~/formation` et que le fichier CSV se trouve à l'emplacement vérifié sur GitHub.

```python
from pathlib import Path
import csv
import matplotlib.pyplot as plt

source = Path("N8N/data/top5_produits.csv")
if not source.is_file():
    raise FileNotFoundError(f"Fichier absent : {source.resolve()}")

with source.open(encoding="utf-8-sig", newline="") as fichier:
    lignes = list(csv.DictReader(fichier))

if not lignes:
    raise ValueError("Le CSV ne contient aucune ligne de produit")

produits = [ligne["product"] for ligne in lignes]
quantites = [int(ligne["quantity"]) for ligne in lignes]

assert len(produits) == len(quantites)
assert all(q >= 0 for q in quantites)

fig, ax = plt.subplots(figsize=(10, 4.5))
barres = ax.bar(produits, quantites)
ax.set_title("Top 5 produits — quantités enregistrées")
ax.set_xlabel("Produit")
ax.set_ylabel("Unités (quantity)")
ax.set_ylim(0, max(quantites) + 6)
ax.tick_params(axis="x", rotation=25)
ax.bar_label(barres, padding=3)
fig.tight_layout()
fig.savefig("/tmp/top5_quantites.png", dpi=150, bbox_inches="tight")
plt.show()
```

**Lecture ligne par ligne :** `Path` situe le fichier ; `utf-8-sig` traite un éventuel marqueur UTF-8 (présent dans le CSV consulté) ; `DictReader` utilise la première ligne comme noms de colonnes ; `int` convertit la quantité ; `fig, ax` adopte le style objet recommandé pour structurer les graphiques ; `bar_label` affiche les valeurs ; `savefig` sauvegarde avant `show` ; `/tmp` évite d'ajouter accidentellement un fichier généré au dépôt Git.

**Résultat attendu avec le fichier versionné :** cinq barres de hauteurs **37, 31, 28, 27, 27**. Cat Food arrive en tête pour la quantité. Ce résultat **ne signifie pas** qu'il arrive en tête pour le revenu.

## 6. Pourquoi `fig, ax` ? Comprendre matplotlib sans copier aveuglément

Le support présente deux interfaces :

```python
# Style pyplot (état implicite) : convenable pour un test simple.
plt.bar(["A", "B"], [3, 5])
plt.title("Exemple")
plt.show()
```

```python
# Style objet : explicite, plus simple à maintenir.
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(["A", "B"], [3, 5])
ax.set_title("Exemple")
fig.tight_layout()
plt.show()
```

La **figure** (`fig`) est le support complet ; l'**axe** (`ax`) est la zone d'un graphique avec coordonnées, titre et graduations. En style objet : `ax.set_title()` au lieu de `plt.title()`, `ax.set_xlabel()` au lieu de `plt.xlabel()`, `ax.tick_params(...)` au lieu de `plt.xticks(...)`.

### Superposition, légende, transparence

```python
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [10, 12, 11], label="Prévu")
ax.plot([1, 2, 3], [9, 13, 10], label="Réalisé", linestyle="--", alpha=0.8)
ax.set_ylabel("Unités")
ax.legend()
plt.show()
```

Les données **Prévu/Réalisé sont illustratives**, inspirées d'un problème professionnel de planning : elles ne proviennent pas de ton ancien employeur. Le `label=` n'apparaît dans la légende qu'après `legend()`. `alpha` contrôle la transparence.

### `**kwargs` : transmettre des options par dictionnaire

```python
options = {"alpha": 0.65, "bins": 8}
ax.hist([1, 2, 2, 3, 5], **options)
```

`**options` transforme les paires du dictionnaire en arguments nommés (`alpha=...`, `bins=...`). C'est le mécanisme montré dans le support pour standardiser le formatage de graphiques dans une boucle. Ne l'utilise que lorsque les noms sont connus et acceptés par la fonction.

### Sous-graphiques : deux mesures différentes, deux axes

```python
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(11, 4))
axes[0].bar(["A", "B"], [12, 20])
axes[0].set_title("Quantité (unités)")
axes[1].bar(["A", "B"], [200, 700])
axes[1].set_title("Revenu (EUR)")
fig.tight_layout()
plt.show()
```

Ces chiffres sont **fictifs**. Les `axes[0]` et `axes[1]` sont deux graphiques **distincts**, chacun avec sa propre échelle. Le support présente aussi `plt.subplot(1, 2, 1)` (style MATLAB), moins explicite pour du code réutilisable.

## 7. Un graphique utile est une vérification, pas une décoration

Ton expérience en prévision, production et analyse économique fournit de bonnes questions à poser avant de publier un graphique :

1. **Source :** CSV brut, SQL, API, résultat d'un modèle ou chiffres imaginés ?
2. **Périmètre :** les cinq produits les plus fréquents, l'ensemble du catalogue, ou cinq exemples ?
3. **Unité :** unités vendues, stock restant, revenu en EUR, secondes, tokens ?
4. **Transformation :** valeurs brutes, agrégation, moyenne, estimation ?
5. **Contrôle :** sommes, types, valeurs manquantes, doublons, ordre, échelle ?
6. **Interprétation :** que peut-on conclure, et surtout que ne peut-on pas conclure ?

**Cas particulier du graphique d'IA :** le rapport Nemotron indique `prompt_tokens=446`, `completion_tokens=106`, `total_tokens=552`. On peut vérifier arithmétiquement **446 + 106 = 552**. Il faut éviter de présenter `tokens_per_second_end_to_end_approx` comme un débit de génération pur : il inclut l'orchestration de bout en bout, d'après les métadonnées du rapport.

**Lien avec RAG :** ton notebook [01_intro.ipynb](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb) montre `Path`, extraction de PDF et `polars`. Les documents extraits peuvent contenir des en-têtes répétés et des tableaux mal structurés : une visualisation construite sur un mauvais extrait donne un résultat propre en apparence mais faux. Il faut valider les données **avant** le graphique.

## 8. Images et limites : `imshow`, RGB, RGBA

Le support montre aussi comment représenter une image ou une matrice avec `imshow` :

```python
import numpy as np
import matplotlib.pyplot as plt

valeurs = np.array([[0, 5, 10], [10, 5, 0]])
plt.imshow(valeurs, cmap="Blues_r")
plt.axis("off")
plt.show()
```

- Un tableau **2D** reçoit une palette via `cmap` ; `_r` inverse cette palette.
- Une image **RGB** possède trois canaux par pixel, **RGBA** quatre, dont un canal alpha pour la transparence ; ses couleurs sont déjà encodées et `cmap` ne joue pas le même rôle.
- Cette compétence est utile à reconnaître pour les images extraites par Docling, mais n'est **pas prioritaire** pour ton positionnement data/BI.

## 9. Entraînement autonome : trois blocs de 45 minutes

**Règle de progression :** avant d'utiliser une aide IA, écrire sur papier le résultat attendu, réaliser une première tentative, puis vérifier. Documenter toute assistance reçue. Ne pas compter une solution copiée comme compétence indépendante.

### Bloc A — Python fiable (45 min, sans graphiques)

1. Dans un nouveau fichier `ex05_controles.py` en dehors du dépôt ou un dossier d'exercices dédié, crée une liste de cinq dictionnaires avec `product`, `quantity`, `revenue_eur` à partir du tableau du §2.
2. Écris une fonction `est_valide(ligne)` vérifiant présence des trois clés, quantité entière non négative, revenu numérique non négatif ; rends `True`/`False`.
3. Affiche les noms des produits avec une quantité d'au moins 30, sans perdre l'ordre initial.
4. Explique la différence entre `sorted(liste)` et `liste.sort()`. Prédire : `resultat = [3, 1].sort()` → quelle valeur ?

**Preuve attendue :** script exécutable, résultat attendu `Cat Food` et `Samsung Galaxy S10` pour l'étape 3, et explication du test.

### Bloc B — Visualisation des données réelles (45 min)

1. Exécute le programme du §5 depuis `~/formation` (d'abord, sans regarder la solution imprimée en détail).
2. Vérifie les cinq hauteurs des barres ; repère où le CSV est chargé et où il est validé.
3. Écris une seconde version qui classe les produits par **revenu décroissant**, en utilisant `revenue_eur` comme valeur et **un titre et un axe corrects**.
4. Enregistre le second graphique dans `/tmp/top5_revenus.png` ; n'affiche pas des unités vendues sur son axe.

**Preuve attendue :** deux images + script, concordance des 5 nombres avec GitHub. Résultat attendu pour le **revenu** : `Generic Motorcycle` en tête.

### Bloc C — Contrôle de présentation et récit métier (45 min)

1. Écris une troisième figure avec deux zones `axes[0]` et `axes[1]`, quantités à gauche, revenus à droite (aucun axe commun).
2. Ajoute titre, axes, rotation des catégories, labels de barres si lisibles, et source « N8N/data/top5_produits.csv ».
3. Rédige trois phrases : **observation**, **limite**, **décision de contrôle**. Exemple de limite acceptable : « Ces cinq produits ne représentent pas nécessairement tout le catalogue ni toute la période ».
4. Identifie deux éléments qui empêcheraient de présenter ce graphique comme une mesure d'activité de l'entreprise.

**Preuve attendue :** PNG lisible + trois phrases + limites. Pour un portfolio professionnel, conserver ensuite une capture, le script et une provenance vérifiable, sans données sensibles.

## 10. Autotest — répondre avant de consulter le corrigé

1. Que renvoie `"a  b".split()` ? Et `"a  b".split(" ")` ?
2. Que change `f"{montant:.2f}"` : la valeur ou seulement son affichage ?
3. Pourquoi `int("27")` fonctionne-t-il, mais pas `int("27 unités")` ?
4. Quelle est la différence entre `is None` et `== 0` ?
5. Pourquoi `l = l.sort()` est-il dangereux ?
6. Pour cinq produits et cinq quantités agrégées, pourquoi `bar`, pas `hist` ?
7. Quelle différence y a-t-il entre `fig` et `ax` ?
8. À quoi sert `**options` dans un appel de fonction ?
9. Pourquoi sauvegarder le fichier avant `plt.show()` dans un script ?
10. Si un diagramme montre un revenu élevé, que ne peut-on pas conclure sur le nombre de ventes ?

### Corrigé succinct

1. `['a', 'b']` ; `['a', '', 'b']`.
2. L'affichage seulement.
3. La seconde chaîne inclut des caractères non numériques ; nettoyer/valider avant conversion.
4. `None` signale une absence ; `0` est un nombre connu.
5. `sort()` renvoie `None` et modifie la liste sur place ; une affectation écrase la variable par `None`.
6. `bar` compare des catégories ; `hist` regroupe les valeurs d'observations numériques par intervalle.
7. `fig` = figure globale ; `ax` = graphique/zone de coordonnées.
8. À transmettre un dictionnaire comme paramètres nommés d'une fonction.
9. L'état de la figure peut changer après `show()` selon le backend / l'environnement ; c'est l'ordre sûr pour une exportation reproductible.
10. Un revenu élevé peut résulter d'un prix unitaire élevé avec peu d'unités ; le revenu n'est pas le nombre de ventes.

### Test de niveau : quatre états, sans notes artificielles

| État | Critère observable | Évaluation après ce cours |
|---|---|---|
| Vu / reconnu | Comprend la syntaxe en la lisant | À autoévaluer |
| Avec guidance | Reproduit un exemple en étant guidé | À autoévaluer |
| Indépendant | Écrit, exécute et corrige sans IA | À démontrer sur bloc B |
| Prouvé | Versionne un script clair, ses contrôles et la provenance | À démontrer après revue de sécurité |

**Critère de sortie du cours 05 :** savoir créer **sans assistance** le graphique des quantités à partir du CSV du dépôt, préciser ses limites et expliquer les cinq opérations `lecture → conversion → validation → visualisation → sauvegarde`. Si ce n'est pas possible, revoir les bases du cours 02 ; ne pas passer du temps sur des images RGBA au détriment de cette compétence.

## 11. Sources et suite

**Support du collègue :** `2026-08-03_10 - Bases Python et visualisation.md` (`2026 Cours.zip`), notes relues du 3 au 10 août 2026. Les remarques sur `eval`, `is`, `match`, `map` et l’ordre des dictionnaires proviennent des mises au point présentes dans ce support.

**Travaux personnels vérifiés le 26/10/2026 :** [top5_produits.csv](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/top5_produits.csv), [rapport_usage_modele.json](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/rapport_usage_modele.json), [B5/app.py](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py) et [notebook RAG d’extraction](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/01_intro.ipynb). Les petites séries « Prévu/Réalisé », « A/B » et `imshow` de ce document sont **pédagogiques, non issues de ton travail professionnel**.

**Cours 06 à suivre :** Python orienté objet (11–14 août 2026) ; il permettra de comprendre les objets `Path`, `fig`, `ax` et `requests.Session` rencontrés dans tes scripts.
