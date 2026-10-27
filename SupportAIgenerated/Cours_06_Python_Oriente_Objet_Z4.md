# Cours personnel 06 — Python orienté objet : comprendre les classes utilisées dans B5 et RAG

**Formation AI Integration Specialist · Consolidation autonome · 26 octobre 2026**  
**Source pédagogique principale :** `2026-08-11_14 - Python orienté objet.md`, dans `2026 Cours.zip` (notes reconstituées par un collègue à partir du cours et des exercices de Robin Pêcheur, 11–14 août 2026).  
**Références professionnelles :** scripts B5 et notebooks RAG versionnés dans `Mircea11/BF_IntegIA_2026`.  
**Durée indicative :** lecture 70–90 min + trois blocs de 45 min.  
**Prérequis :** variables, fonctions, listes, dictionnaires, exceptions élémentaires (cours 02 et 05). Aucun service Docker, modèle GPU ni base de données requis pour les exercices.

> **Compétence visée :** lire une classe Python, identifier son état et ses comportements, créer un objet simple qui protège une règle métier, tester ses erreurs et décider quand une classe apporte plus de valeur qu'une fonction. L'exposition aux classes du dépôt ne constitue pas une preuve de maîtrise autonome.

## 1. D'où vient le cours et ce que nous pouvons réellement prouver

Le support du collègue suit quatre exercices de formation : **Voiture** (attributs, opérateurs, héritage), **Animaux** (abstraction), **Banque** (état, contraintes, exceptions), **Jeu héros/monstres** (composition, sous-classes, organisation en paquets). Il détaille aussi des défauts observés dans des fichiers de cours. **Ces observations sont celles du collègue** : je n'ai pas eu accès à l'intégralité de son dépôt `IA/Base_Python/POO` pour les reproduire.

Ton GitHub vérifié donne trois correspondances utiles :

| Preuve visible sur GitHub | Ce qu'elle démontre | Ce qu'elle ne démontre pas |
|---|---|---|
| [`N8N/B5_conseiller_produit_v2/app.py` — lignes 11–35](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py#L11-L35) | `class ChatIn(BaseModel)` ; `requests.Session()` ; instance `FastAPI(...)` | Que tu sais programmer seul une classe et son constructeur |
| [`N8N/B5_conseiller_produit_v2/test_b5.py` — lignes 1–37](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py#L1-L37) | `class B5Tests(unittest.TestCase)` ; `self`, `setUp`, `tearDown` | Que les tests simulés démontrent à eux seuls le comportement en production |
| [`RAG/.../demo_live/demo_chunking_embedding.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb) | Création et emploi de `DocumentConverter` et `HybridChunker`, classes de bibliothèques | Que tu en connais l'implémentation interne |

**Diagnostic de départ :** tu utilises déjà des objets dans des systèmes complets (B5, RAG). En revanche, aucune de ces références ne prouve que tu peux **construire, expliquer et tester indépendamment** une classe. Le cours vise ce passage précis, sans réécrire tes workflows existants.

## 2. Une classe, un objet, une fonction : trois choses à distinguer

Une **classe** définit une structure et un comportement. Une **instance** est un objet particulier construit à partir de cette classe. `self` désigne l'instance courante ; `__init__` l'initialise après sa création. Une **fonction** reste préférable lorsqu'on n'a pas besoin d'un état persistant lié à un objet.

### 2.1 Exemple de ton métier : un produit à contrôler

Les données suivantes sont **fictives**, pour apprendre ; elles ne sont pas un relevé du catalogue DummyJSON.

```python
class Produit:
    def __init__(self, nom, prix, stock):
        self.nom = nom
        self.prix = prix
        self.stock = stock

    def est_disponible(self):
        return self.stock > 0

ballon = Produit("Ballon", 20.0, 0)
raquette = Produit("Raquette", 35.0, 4)

print(ballon.nom)                 # Ballon
print(ballon.est_disponible())    # False
print(raquette.est_disponible())  # True
```

**Lecture ligne par ligne :** `class Produit` est le modèle ; `ballon` et `raquette` sont deux instances distinctes ; `self.stock` appartient à chaque instance ; `est_disponible` agit sur le stock de l'objet appelé.

| Élément | Dans l'exemple | Sens |
|---|---|---|
| Classe | `Produit` | Définition commune |
| Instance | `ballon` | Produit particulier |
| Attribut d'instance | `ballon.stock` | Valeur propre à ce produit |
| Méthode d'instance | `ballon.est_disponible()` | Calcul qui lit son état |
| Constructeur d'initialisation | `__init__` | Initialise les attributs |

**Question de compréhension :** si tu écris `raquette.stock = 0`, est-ce que `ballon.stock` change ? **Non.** Ce sont deux instances distinctes.

### 2.2 Attribut de classe : partagé, contrairement à `self.stock`

Le support utilise `Voiture.dernier_id` pour compter les créations :

```python
class Compteur:
    total = 0               # Attribut de classe

    def __init__(self):
        Compteur.total += 1
        self.numero = Compteur.total  # Attribut d'instance

un = Compteur()
deux = Compteur()
assert Compteur.total == 2
assert un.numero == 1
assert deux.numero == 2
```

**Piège :** `self.total += 1` crée généralement un attribut sur l'instance et masque l'attribut de classe. Un compteur Python local n'est pas un identifiant durable ou distribué ; pour de vrais messages B5, on préfère l'identifiant de PostgreSQL.

## 3. Encapsulation : empêcher un produit invalide

Dans un catalogue, un stock négatif ou un prix négatif doit être rejeté **avant** une recommandation. Le support distingue `nom` (public), `_nom` (interne par convention), `__nom` (renommage automatique, *name mangling*). Aucun de ces préfixes ne garantit la confidentialité ou l'impossibilité d'accès en Python.

Une **propriété** permet de contrôler les affectations. Voici une classe autonome complète :

```python
class Produit:
    def __init__(self, nom: str, prix: float, stock: int):
        self.nom = nom
        self.prix = prix     # Passe par le setter
        self.stock = stock   # Passe par le setter

    @property
    def prix(self) -> float:
        return self._prix

    @prix.setter
    def prix(self, valeur: float) -> None:
        if valeur < 0:
            raise ValueError("Le prix doit être positif ou nul")
        self._prix = valeur

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, valeur: int) -> None:
        if type(valeur) is not int or valeur < 0:
            raise ValueError("Le stock doit être un entier positif ou nul")
        self._stock = valeur

    def est_disponible(self) -> bool:
        return self.stock > 0

p = Produit("Ballon", 20.0, 0)
assert p.est_disponible() is False
p.stock = 3
assert p.est_disponible() is True
```

Pourquoi `type(valeur) is not int` et non simplement `isinstance(valeur, int)` ? Parce qu'en Python `True` est aussi une instance de `int`. Le contrôle proposé refuse `True` comme stock. **La validation ci-dessus reste une règle simplifiée** : en production, il faut aussi décider comment gérer `float('nan')`, la monnaie, les décimales et les données externes mal typées.

**Lien B5 :** une classe peut porter l'état d'un produit ; la **vérité sur le stock** doit toujours venir d'une source actualisée. Un objet Python, à lui seul, ne garantit pas que son stock est à jour.

### Le piège des valeurs par défaut mutables

Le support présente le problème du dictionnaire partagé :

```python
# À éviter : la même liste est partagée entre instances.
def __init__(self, produits=[]):
    self.produits = produits

# Préférable : une nouvelle liste si rien n'a été fourni.
def __init__(self, produits=None):
    self.produits = [] if produits is None else list(produits)
```

Dans un projet de données, partager accidentellement une liste entre deux sessions clients peut provoquer des erreurs de résultat ou de confidentialité.

## 4. `__str__`, `__repr__` et les méthodes spéciales

Les méthodes entourées de doubles soulignés (*dunder*) définissent le comportement de l'objet avec le langage :

| Méthode | Opération | Utilité |
|---|---|---|
| `__init__` | `Produit(...)` | Initialise |
| `__str__` | `print(produit)` | Texte pour un utilisateur |
| `__repr__` | `repr(produit)` | Représentation pour déboguer |
| `__eq__` | `a == b` | Égalité définie par le métier |
| `__add__` | `a + b` | Calcule une nouvelle valeur |
| `__iadd__` | `a += b` | Opération augmentée, peut modifier l'objet |

```python
class Stock:
    def __init__(self, quantite):
        if quantite < 0:
            raise ValueError("Stock négatif")
        self.quantite = quantite

    def __str__(self):
        return f"{self.quantite} unités"

    def __add__(self, autre):
        if not isinstance(autre, Stock):
            return NotImplemented
        return Stock(self.quantite + autre.quantite)

ancien = Stock(3)
reception = Stock(5)
nouveau = ancien + reception
assert nouveau.quantite == 8
assert ancien.quantite == 3  # __add__ ne change pas ancien
```

Le support souligne une erreur de conception fréquente : coder une **mutation** à l'intérieur de `__add__` rend l'opérateur `+` surprenant. Pour une mise à jour explicite, une méthode `ajouter_stock()` est souvent plus lisible qu'une surcharge d'opérateur. Les méthodes spéciales sont utiles, mais ne doivent pas masquer les règles métier.

## 5. Héritage, `super()` et composition : choisir une structure

**Héritage = « est un »** : `CompteEpargne` est un `Compte`. **Composition = « a un »** : un `Catalogue` a plusieurs produits.

```python
class Produit:
    def __init__(self, nom):
        self.nom = nom

class ProduitNumerique(Produit):
    def __init__(self, nom, licence):
        super().__init__(nom)
        self.licence = licence

manuel = ProduitNumerique("Guide PDF", "personnelle")
assert isinstance(manuel, Produit)
```

`super().__init__(nom)` réutilise l'initialisation de la classe parent selon l'ordre de résolution des méthodes (MRO). Le support aborde aussi l'héritage multiple, où cet ordre mérite une attention particulière : `Classe.__mro__` montre les classes recherchées. L'appel manuel successif de plusieurs constructeurs de parents, vu dans un exercice « voiture amphibie », ne constitue pas une recette générale pour les hiérarchies complexes.

**Composition, souvent préférable dans B5 :**

```python
class Catalogue:
    def __init__(self, produits=None):
        self.produits = [] if produits is None else list(produits)

    def disponibles(self):
        return [p for p in self.produits if p.est_disponible()]
```

Un catalogue n'**est pas un** produit. Il **contient** des produits. N'ajoute pas une classe pour chaque petit traitement Python : lorsque deux fonctions simples suffisent, leur simplicité peut être un avantage.

### `@staticmethod` et `@classmethod`

```python
class Prix:
    @staticmethod
    def est_valide(valeur):
        return isinstance(valeur, (int, float)) and valeur >= 0

    @classmethod
    def depuis_texte(cls, texte):
        return cls(float(texte.replace(",", ".")))

    def __init__(self, valeur):
        self.valeur = valeur
```

- Une méthode **statique** ne reçoit ni `self` ni `cls` : elle ressemble à une fonction rangée dans la classe.
- Une méthode de **classe** reçoit `cls`, utile notamment pour un constructeur alternatif.
- Le support indique que `@classmethod` n'était pas travaillé dans les exercices : à ce stade, le **reconnaître** suffit ; pas besoin d'en faire une priorité.

## 6. Classes abstraites et polymorphisme : pourquoi cela existe

Dans l'exercice **Banque**, le support introduit une classe abstraite `Compte` et une méthode `calcul_interet()` que chaque sous-classe doit implémenter. Les taux de cet exercice (4,5 %, 3 %, 9,75 %) **appartiennent uniquement à la simulation pédagogique**, pas à une recommandation financière.

```python
from abc import ABC, abstractmethod

class RegleDisponibilite(ABC):
    @abstractmethod
    def accepter(self, stock: int) -> bool:
        ...

class EnStock(RegleDisponibilite):
    def accepter(self, stock: int) -> bool:
        return stock > 0

regle = EnStock()
assert regle.accepter(3) is True
assert regle.accepter(0) is False
```

Une classe abstraite ne doit pas être instanciée directement tant que ses méthodes abstraites ne sont pas implémentées. Le **polymorphisme** permet d'appeler la même interface `accepter()` avec plusieurs règles différentes. C'est utile quand plusieurs stratégies ont réellement une raison d'exister ; pour B5 en l'état, une simple fonction `stock > 0` reste souvent suffisante.

## 7. Exceptions personnalisées : distinguer erreur de donnée et rupture de stock

Le support emploie `SoldeInsuffisantException` dans l'exercice Banque. Pour transposer le principe :

```python
class ProduitIndisponible(Exception):
    pass

def reserver(produit, quantite):
    if quantite <= 0:
        raise ValueError("Quantité demandée invalide")
    if quantite > produit.stock:
        raise ProduitIndisponible("Stock insuffisant")
    produit.stock -= quantite

p = Produit("Ballon", 20.0, 2)  # Reprendre la classe du §3
try:
    reserver(p, 3)
except ProduitIndisponible as exc:
    print(f"Impossible de réserver : {exc}")
```

Ici, `ValueError` signifie « entrée invalide » ; `ProduitIndisponible` signifie « commande valide en principe, mais impossible avec cet état de stock ». Cette distinction facilite les messages utilisateurs et les tests. **Attention :** ce petit exercice n'est pas un système de réservation concurrent ; en application réelle, la vérification et la modification de stock devraient être atomiques côté serveur/base de données.

## 8. Reconnaître la POO dans ton GitHub, sans la surévaluer

### 8.1 B5 : une classe héritée pour vérifier les messages entrants

Extrait vérifié de [`app.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py#L27-L35) :

```python
app = FastAPI(title='B.5 Conseiller Produit - local Z4')
http = requests.Session()

class ChatIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=2000)
```

- `FastAPI(...)` et `requests.Session()` produisent des **instances**.
- `ChatIn` **hérite de `BaseModel`** (Pydantic) ; `Field(...)` précise les contraintes à appliquer aux entrées. Contrairement aux annotations Python ordinaires, **Pydantic effectue une validation à l'exécution**.
- `session_id` est crucial pour séparer les conversations. Le nom `ChatIn` décrit un schéma de données, pas un appel à un modèle IA.

### 8.2 Les tests B5 : `self` apparaît dans un vrai projet

Extrait vérifié de [`test_b5.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py#L9-L37) :

```python
class B5Tests(unittest.TestCase):
    def setUp(self):
        self.products = []
        self.points = {}
        self.names = {}
        self.messages = {}
```

- `unittest.TestCase` est la **classe parente** ; `B5Tests` est une sous-classe.
- `setUp` prépare **un état de test isolé** avant chaque test ; `tearDown` restaure certaines fonctions simulées après l'exécution.
- Le programme construit **194 produits fictifs** pour les tests hors ligne. Cela **ne prouve pas** que le vrai Qdrant du Z4 contient 194 points à cet instant.

### 8.3 Le pipeline RAG : utiliser des objets de bibliothèque

Le notebook [`demo_chunking_embedding.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb) importe `DocumentConverter` et `HybridChunker`. L'enchaînement est : **on importe une classe → on construit un objet configuré → on appelle ses méthodes sur des documents**.

**Règle de lecture :** quand une ligne est `objet.methode(...)`, identifie d'abord **quel objet** reçoit la méthode et **quel état** il possède. Si tu ne peux pas l'expliquer, remonte à l'endroit où l'objet est construit.

### 8.4 Organisation des modules

Le support montre un jeu découpé en `main.py`, `models/`, puis sous-dossiers des personnages. Retenir la règle : une responsabilité claire par module et des imports compréhensibles. `if __name__ == "__main__":` garde le code de démonstration hors des imports. Une classe par fichier est une **convention possible**, pas une obligation Python.

## 9. Erreurs et pièges du support : points à reconnaître

Les notes du collègue signalent plusieurs erreurs dans les exercices de formation. Elles sont utiles comme **exemples de diagnostic**, non comme constats vérifiés sur ton dépôt :

| Cas du support | Problème pédagogique | Principe à retenir |
|---|---|---|
| `other >= 0 ^ self.solde >= 0` | Priorité des opérateurs et usage de `^` | Parenthéser les expressions ; en Python, `^` est XOR bit à bit |
| `VoitureAmphibie.accelerer()` | Signature de méthode modifiée | Une sous-classe ne doit pas surprendre le code client |
| `Banque.__add__` renvoie `None` | Opérateur mal défini | `+` doit produire un résultat intelligible |
| `Chien` reste abstraite | Méthode `@abstractmethod` non implémentée | Vérifier pourquoi une classe est instanciable ou non |
| `modificateur(...)` sans qualification | Nom non défini dans le contexte | Préciser `self.`, `Classe.` ou importer selon le cas |
| `Personnage` dans sa propre annotation | Référence avancée à un type | Utiliser `"Personnage"` ou des annotations différées si nécessaire |

**Méthode face à une erreur :** reproduire le cas minimal → lire le type d'exception → localiser la ligne → expliquer *pourquoi* avant de changer le code → ajouter un test qui éviterait sa réapparition.

## 10. Programme d'étude sur une journée libre : 3 × 45 minutes

### Bloc A — Lecture active : comprendre deux classes (45 min)

1. Sans IA, ouvre `N8N/B5_conseiller_produit_v2/app.py`. Localise `ChatIn` ; note son parent, ses deux champs et leurs limites.
2. Ouvre `N8N/B5_conseiller_produit_v2/test_b5.py`. Localise `B5Tests`, `setUp`, `tearDown` et deux usages de `self`.
3. Dessine sur papier : `B5Tests` → `unittest.TestCase` ; `ChatIn` → `BaseModel` ; `Catalogue` contient plusieurs `Produit`.
4. Explique à voix haute : pourquoi `requests.Session()` est une instance, mais `requests` est un module.

**Preuve exigée :** 8–12 lignes de notes avec références aux fichiers, sans recopier l'explication de ce cours.

### Bloc B — Code personnel : classe Produit (45 min)

Créer localement un nouveau fichier **hors des scripts B5 fonctionnels**, par exemple `~/formation_exercices/poo06_produit.py`. Sans copier le code du §3, écrire une classe `Produit` qui :

- accepte `nom`, `prix`, `stock` au constructeur ;
- refuse `prix < 0`, `stock < 0` et `stock` non entier ;
- expose `est_disponible()` et une représentation `__str__` ;
- permet de modifier le stock en conservant la validation.

**Tests attendus, à écrire toi-même :**

```python
p = Produit("Ballon", 20.0, 0)
assert not p.est_disponible()
p.stock = 2
assert p.est_disponible()
try:
    p.stock = -1
    raise AssertionError("Le stock négatif aurait dû être refusé")
except ValueError:
    pass
```

**Preuve exigée :** `python3 poo06_produit.py` termine sans erreur, avec au moins trois assertions supplémentaires de ton choix.

### Bloc C — Composition et test (45 min)

Créer `Catalogue` qui contient des produits, puis coder `disponibles()`. Interdire le retour d'un produit avec `stock == 0`. Tester avec **trois produits fictifs**, dont deux disponibles.

**Critères :**

1. Une classe `Produit` ne modifie pas les autres instances.
2. `Catalogue.disponibles()` renvoie exactement deux objets.
3. Modifier un stock change le résultat à l'appel suivant.
4. Un prix ou un stock invalide est rejeté.
5. Tu peux expliquer pourquoi **composition** et non héritage.

**Livrable local facultatif :** deux petits fichiers (`poo06_produit.py`, `test_poo06.py`), conservés pour évaluation. Aucun besoin de pousser immédiatement sur GitHub ni de toucher au conteneur Docker.

## 11. Autoévaluation — 10 questions (sans consulter le corrigé)

1. Quelle est la différence entre une classe et une instance ?
2. Que fait `self` dans `ballon.est_disponible()` ?
3. Pourquoi un attribut de classe compteur est-il différent de `self.stock` ?
4. Quelle erreur peut provoquer `def __init__(self, produits=[])` ?
5. Quelle est la différence entre `@property` et une méthode appelée avec `()` ?
6. Pourquoi un `Catalogue` contenant des `Produit` utilise-t-il plutôt la composition ?
7. À quoi sert `super().__init__(...)` dans une classe enfant ?
8. Pourquoi `__add__` ne doit-il généralement pas modifier silencieusement l'opérande gauche ?
9. Quelle est la différence entre `ValueError` et une exception personnalisée `ProduitIndisponible` ?
10. Pourquoi le passage de 194 produits dans les tests simulés ne prouve-t-il pas l'état de Qdrant en production ?

**Barème :** 1 point par réponse correcte avec justification. 8/10 est un bon niveau de compréhension, **mais la maîtrise autonome requiert aussi le code du bloc B/C réalisé sans assistance**.

### Corrigé synthétique

1. La classe définit ; l'instance est un objet concret de ce type.
2. Il désigne l'instance `ballon` dont on lit le stock.
3. L'attribut de classe est partagé ; `self.stock` appartient à une instance.
4. La même liste est réutilisée par plusieurs instances.
5. La propriété s'utilise comme un attribut et peut valider une affectation ; une méthode est explicitement appelée.
6. Un catalogue **a** des produits ; il n'**est pas** un produit.
7. Il réutilise l'initialisation prévue par la hiérarchie selon la MRO.
8. Parce que `a + b` est normalement compris comme une opération produisant une valeur, non une mutation surprenante de `a`.
9. `ValueError` : donnée/argument invalide ; exception personnalisée : situation métier spécifique qu'on veut intercepter distinctement.
10. Les tests utilisent des produits simulés et non un comptage du service Qdrant réel.

## 12. Validation de compétence et suite du parcours

| Compétence | Niveau démontré par les références existantes | Preuve d'autonomie attendue |
|---|---|---|
| Reconnaître `class`, instance, héritage | Présence dans les scripts du dépôt, usage au moins avec assistance | Expliquer `ChatIn` et `B5Tests` sans notes |
| Écrire `__init__`, méthodes et propriétés | **Non démontré indépendamment** | Réussir le bloc B seul |
| Gérer les exceptions de validation | Utilisé dans les scripts du projet | Démontrer deux erreurs et les capturer proprement |
| Composition | Reconnue dans les bibliothèques/outils | Réussir le bloc C et justifier « a un » |
| ABC, méthodes spéciales, MRO | Vus dans les notes du support | Reconnaissance et explication simples ; approfondissement ultérieur |

**Niveaux à consigner après exercice :** **V** = vu/reconnu ; **G** = réalisé avec guidage ; **I** = réalisé indépendamment ; **P** = prouvé par un exercice reproductible. Ne pas convertir automatiquement « code présent sur GitHub » en **I** ou **P**.

**Priorité à 90 jours :** utiliser la POO pour mieux lire, maintenir et tester le code du pipeline « intake → structuration → validation → résultat », sans lancer une refonte de B5. Le cours suivant du support (17–21 août) traite **SQLAlchemy, `requests` et `async`**, qui relient les objets Python aux bases SQL et aux API.

## Sources et provenance

- **Support principal :** `2026 Cours.zip` → `2026-08-11_14 - Python orienté objet.md`. Il synthétise des exercices d'une autre personne et des commentaires de correction ; ces corrections **n'ont pas été reproduites ici sur son dépôt d'origine**.
- **Code vérifié :** [`app.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py), [`test_b5.py`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py), [`demo_chunking_embedding.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb).
- **Exemples `Produit`, `Catalogue`, `Stock`, `Prix` :** exemples pédagogiques conçus pour ce cours ; **pas** des copies de classes actuellement présentes dans B5.
- **État de compétence :** inférence prudente à partir du code vérifié et de nos exercices accompagnés, et non résultat d'un test autonome en direct.
