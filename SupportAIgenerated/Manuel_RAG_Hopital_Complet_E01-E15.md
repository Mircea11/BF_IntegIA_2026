# Manuel d’apprentissage — RAG Hôpital de Valmont

**Partie I · Des documents à la comparaison Dense / Sparse / Hybride (jusqu’à E10)**  
**État vérifié : 30 octobre 2026 · Dépôt : `Mircea11/BF_IntegIA_2026` · Commit : `1369025`**  
**Destinataire : autoformation, Formation AI Integration Specialist — Bruxelles Formation**

> **Périmètre.** Ce manuel explique ce qui a été construit et effectivement testé avant E11. Il sert à **comprendre, reproduire et expliquer** le travail, et non à présenter comme terminées les étapes encore absentes. **La Partie II commencera à E11 : reranking, puis étapes suivantes.**
>
> **Origine des informations.** Les descriptions des modules viennent du code enregistré dans `RAG/rag-hopital/` ; les exigences viennent de `exercice_03_recap_enonce.md` et des notebooks de cours `04_intro_qdrant.ipynb`, `05_advanced_filtering_and_reranker.ipynb`, `06_evaluation.ipynb` ; les métriques proviennent des sorties PostgreSQL des expériences 3, 5 et 6 communiquées lors du travail pratique. Les exemples pédagogiques simplifiés sont identifiés comme tels.

## Comment utiliser ce manuel

- **Lecture de 15 minutes :** résumé exécutif, schéma général, chapitre sur les métriques, résultats, état des lieux.
- **Lecture de 45 minutes :** ajouter les chapitres sur Python, Qdrant, PostgreSQL et TOML.
- **Étude approfondie :** travailler les exercices sans regarder les corrigés ; ouvrir les fichiers du dépôt indiqués.
- **Règle de compétence :** **vu** (je reconnais), **guidé** (je réussis avec instructions), **autonome** (je reproduis sans aide), **prouvé** (je démontre et vérifie le résultat). Exécuter un script fourni par l’IA ne prouve pas, à lui seul, une maîtrise autonome.

---

# 1. Bilan : jusqu’où sommes-nous arrivés ?

## 1.1 Résultats vérifiés

| Élément | Résultat | Signification |
|---|---:|---|
| Documents du corpus | **280** | 247 documents de patients fictifs + 33 notices de médicaments. |
| Chunks indexés | **1 173** | Morceaux de texte pouvant être retrouvés indépendamment. |
| Limite de taille de chunk | **512 tokens** | Le script valide `token_count <= 512`. |
| Dimension dense BGE-M3 | **1 024** | Chaque chunk dense est représenté par 1 024 valeurs numériques. |
| Questions du jeu d’évaluation | **106** | 100 avec preuves, 6 `out_of_corpus`. |
| Expérience 3 | **Dense, 100 questions** | Référence interne pour les méthodes de recherche. |
| Expérience 5 | **Sparse BM25, 100 questions** | Recherche lexicale indépendante. |
| Expérience 6 | **Hybrid RRF, 100 questions** | Combinaison Dense + Sparse. |
| Base d’expériences | **PostgreSQL** | Configurations, résultats par question, métriques. |
| Dernier point de sauvegarde Git | **`1369025`** | Code et configurations synchronisés avec `origin/main`. |

**Conclusion correcte :** nous disposons d’un **moteur de retrieval et d’un banc d’évaluation automatisé**. Nous n’avons **pas encore** un RAG complet produisant des réponses avec un LLM et jugeant les refus.

## 1.2 Repères de progression

| Étape de notre parcours | Travail réalisé | État |
|---|---|---|
| E01–E06 — Fondations ETL | Projet Python, services, conversion, chunks, métadonnées, tests | Fait |
| E07 — Indexation | Embeddings BGE-M3 et 1 173 points dans Qdrant | Fait |
| E08 — Retrieval dense | Rechercher et classer les chunks | Fait |
| E09 — Évaluation / PostgreSQL | Vérité terrain, métriques, expérience persistante | Fait |
| E10 — BM25 / Hybride / TOML | Index hybride, 3 méthodes, 100 questions chacune | Fait |
| **E11 — Reranker** | Réordonner un pool de candidats avec BGE-Reranker-v2-M3 | **Non commencé dans cette partie** |

Ces identifiants E01–E11 sont **notre découpage de travail**, pas nécessairement la numérotation des sections du document du professeur.

---

# 2. Comprendre l’objectif du projet

## 2.1 Le problème à résoudre

Un utilisateur pose une question à partir de nombreux documents. Un modèle génératif ne peut ni garantir qu’il connaît les données internes, ni décider spontanément quel document est à jour. Le **RAG — Retrieval-Augmented Generation** cherche d’abord les passages pertinents, puis les transmet à un modèle de langage pour construire une réponse appuyée sur les sources.

**Aujourd’hui, notre application s’arrête au retrieval :**

```text
280 documents hospitaliers fictifs
         │
         ▼
    Docling (conversion)
         │
         ▼
   JSON structurés
         │
         ▼
Découpage + métadonnées patient
         │
         ▼
      1 173 chunks
         │
         ▼
  Embeddings / index Qdrant
         │
Question ─► Dense / Sparse / Hybrid ─► Top 5 chunks
                                      │
                                      ▼
                       Comparaison à la vérité terrain
                                      │
                                      ▼
                           Scores dans PostgreSQL

       [E11 et après : reranker, génération, juge]
```

## 2.2 Pourquoi des données synthétiques ?

Le Centre Hospitalier de Valmont est fictif. Les patients, données médicales et documents sont inventés pour l’exercice. C’est essentiel pour apprendre des techniques applicables aux données de santé sans divulguer de véritables dossiers médicaux. Les posologies sont des données de test, **pas des recommandations médicales**.

## 2.3 Trois verbes différents

- **Ingérer / ETL :** préparer les documents et les données.
- **Retrouver / retrieval :** choisir les passages susceptibles de répondre.
- **Générer :** rédiger une réponse à partir des passages. **Pas encore implémenté.**

**Question de compréhension :** si Qdrant retrouve cinq bons extraits mais qu’aucun LLM n’a produit de réponse, le projet a-t-il déjà une réponse RAG ? **Non : il possède le contexte nécessaire, pas la réponse générée.**

---

# 3. Organisation du projet : où se trouve chaque responsabilité ?

La racine de travail sur la station est :

```bash
cd ~/formation/RAG/rag-hopital
```

L’architecture pertinente est :

```text
rag-hopital/
├── pyproject.toml           # Dépendances Python du sous-projet
├── uv.lock                 # Versions résolues pour ce sous-projet
├── docker-compose.yml      # PostgreSQL et Qdrant
├── .env                    # Variables privées, JAMAIS committées
├── experiments/
│   ├── sparse_bm25.toml
│   └── hybrid_bge_bm25.toml
├── data/
│   ├── hopital/            # Documents et référentiels locaux
│   ├── conversions/        # JSON produits par Docling
│   └── chunks/chunks.jsonl # Sortie générée (non suivie par Git)
├── scripts/
│   ├── ingest.py           # Conversion
│   ├── chunk_corpus.py     # Fabrication des chunks
│   ├── index_corpus.py     # Indexation
│   ├── run_experiment.py   # Expériences TOML et réévaluations
│   └── ...                 # Tests pédagogiques et diagnostics
└── src/rag_hopital/
    ├── config.py           # Paramètres machine et chemins
    ├── db.py               # Fonctions PostgreSQL
    ├── etl/
    │   ├── convert.py      # Docling
    │   ├── chunk.py        # HybridChunker
    │   ├── index.py        # Embeddings et Qdrant
    │   └── log_etl.py      # Journal ETL
    ├── rag/
    │   └── search.py       # Dense, Sparse, Hybrid
    └── evaluation/
        ├── metrics.py      # Grades, couverture, nDCG
        └── runner.py       # Évaluation automatique
```

**Important :** l’absence d’un fichier dans ce schéma abrégé ne veut pas dire qu’il n’existe pas ; il montre les éléments utiles pour E01–E10.

### Pourquoi séparer `src/` et `scripts/` ?

`src/` contient la logique réutilisable. Les scripts sont des points d’entrée : ils lisent les arguments et appellent les fonctions. Cela rend la même logique utilisable plus tard depuis un notebook, une API ou une interface.

**Exemple :** `scripts/run_experiment.py` décide de la configuration et des questions ; `rag/search.py` sait **comment** interroger Qdrant.

---

# 4. Environnement technique : Python, uv, Docker et Git

## 4.1 Les différents rôles

| Outil | Fonction dans ce projet |
|---|---|
| Python 3.12 | Exécuter le code de l’application. |
| `uv` | Gérer l’environnement Python et les dépendances du sous-projet. |
| `pyproject.toml` | Déclarer les dépendances directes (`docling`, `qdrant-client`, `psycopg`, `fastembed`, etc.). |
| `uv.lock` | Conserver les versions résolues pour des installations reproductibles. |
| Docker Compose | Démarrer PostgreSQL et Qdrant avec leurs volumes. |
| PostgreSQL | Mémoriser les expériences et leurs scores. |
| Qdrant | Stocker les vecteurs et retrouver les chunks. |
| Git / GitHub | Versionner le code et les configurations, **pas** les bases locales. |
| `.env` | Fournir des variables comme les URLs et secrets de connexion. |

Deux commandes différentes :

```bash
uv run python scripts/run_experiment.py --help   # Exécute dans l'environnement du projet
python scripts/run_experiment.py --help          # Peut utiliser un autre Python !
```

**Astuce diagnostique :** `uv run python -c "import sys; print(sys.executable)"` montre le Python réellement utilisé.

## 4.2 Les services ne sont pas les bibliothèques

`qdrant-client` est une **bibliothèque Python**. Qdrant est un **serveur / moteur de base vectorielle**. Installer le client ne démarre pas Qdrant. De même, `psycopg` est un client PostgreSQL, pas la base elle-même.

Vérifications en lecture seule :

```bash
docker compose ps
curl -s http://localhost:6333
```

## 4.3 Git : ce que la sauvegarde protège et ne protège pas

Le commit validé `1369025` protège le code de l’étape E10. Dans `~/formation`, la **racine Git** est plus haute que le sous-projet `rag-hopital` : les règles du `.gitignore` racine s’y appliquent.

Exclusions vérifiées :

```gitignore
/RAG/rag-hopital/data/chunks/
/RAG/rag-hopital/data/conversions_enriched/
```

Les données générées peuvent rester localement tout en étant exclues de Git. `git rm --cached` retire un fichier de l’index Git **sans le supprimer de la machine**.

**Ne pas confondre :** un `git push` ne sauvegarde pas les volumes Docker `postgres_data` et `qdrant_data`. Le code peut être récupéré depuis GitHub, mais les résultats locaux exigent une **stratégie de sauvegarde distincte**.

---

# 5. ETL — Transformer des documents en données exploitables

ETL signifie **Extract, Transform, Load** : extraire, transformer, charger. Dans notre projet, l’ETL devient une succession d’étapes vérifiables.

## 5.1 Conversion avec Docling

Sources : DOCX, PDF et éventuellement d’autres formats pris en charge. `src/rag_hopital/etl/convert.py` configure Docling, active notamment la reconnaissance des tableaux et l’OCR pour les formats concernés, puis exporte un **JSON structuré**.

Pourquoi ne pas extraire seulement du texte brut ? Un tableau biologique n’est pas une phrase ordinaire : ses lignes, colonnes et intitulés portent le sens. Docling vise à préserver des structures utiles pour la suite.

Dans le code :

```python
result = converter.convert(source)
result.document.save_as_json(output, image_mode=ImageRefMode.EMBEDDED)
```

**Lecture :** `convert()` produit un objet représentant le document ; `save_as_json()` l’enregistre. Le JSON préserve davantage de structure qu’un simple fichier `.txt`.

### Les vérifications importantes

- Le document a-t-il été traité avec succès ?
- La sortie existe-t-elle au chemin prévu ?
- Les tableaux et en-têtes sont-ils lisibles ?
- Le fichier est-il une **sortie générée** ou une **source à versionner** ?

L’option `force=False` permet de ne pas reconvertir systématiquement des sorties déjà présentes.

## 5.2 Découpage avec Docling `HybridChunker`

Le système ne recherche pas un document entier comme une unité unique : il recherche des **chunks**. `src/rag_hopital/etl/chunk.py` emploie un tokenizer de BGE-M3 et `HybridChunker`.

Notre règle de production : **512 tokens au maximum**, avec une réserve pour une ligne d’identification du patient.

Exemple simplifié de texte préparé :

```text
Patient: M. Jean SIMON | IPP: 4100021
Bilan biologique d'avril 2025
HbA1c : 8,5 %
```

La ligne patient est importante parce qu’après découpage un fragment « HbA1c : 8,5 % » pourrait autrement être confondu avec un résultat d’un autre patient. **Elle réduit un risque ; elle ne garantit pas l’absence de confusion.**

Le script `scripts/chunk_corpus.py` a confirmé :

- **280 documents** traités ;
- **1 173 chunks** produits ;
- contrôle `assert token_count <= 512` ;
- snapshot `baseline_v1` indiquant un **maximum observé de 371 tokens**.

Le maximum 512 est une **limite configurée**, non la taille effective de chaque chunk. Il est parfaitement normal que les chunks aient des longueurs différentes.

## 5.3 Métadonnées et JSONL

Chaque ligne du fichier `data/chunks/chunks.jsonl` est un **objet JSON indépendant**. C’est le format **JSON Lines** : un enregistrement par ligne.

Exemple simplifié :

```json
{"document":"4100021_2025-04-11_bilan.docx","chunk_index":1,"chunk_id":"4100021_2025-04-11_bilan.docx::1","patient_ipp":"4100021","text":"..."}
```

- `document` identifie le document d’origine.
- `chunk_index` identifie la position du morceau dans le document.
- `chunk_id` identifie de manière stable ce chunk.
- `patient_ipp` sert à contextualiser ou filtrer de futures recherches.
- `text` fournit le contenu à convertir en vecteurs.

### Point de Python : lire un JSONL

```python
import json
from pathlib import Path

path = Path("data/chunks/chunks.jsonl")
with path.open(encoding="utf-8") as file:
    for line in file:                  # Une ligne à la fois, sans tout charger
        record = json.loads(line)      # Texte JSON -> dictionnaire Python
        print(record["chunk_id"])    # Accéder à une valeur par sa clé
        break                         # Premier exemple seulement
```

**Exercice :** expliquer la différence entre `json.loads(line)` et `json.load(file)`.

---

# 6. Embeddings, vecteurs et indexation dans Qdrant

## 6.1 Qu’est-ce qu’un embedding ?

Un **embedding** est une représentation numérique d’un texte destinée à rapprocher les contenus de sens similaire. Pour notre BGE-M3 dense, un texte est associé à un vecteur de **1 024 composantes**.

Exemple **schématique** (pas une sortie réelle du modèle) :

```python
[0.12, -0.31, 0.05, 0.80, ...]  # 1 024 valeurs au total
```

Le texte **et** la question doivent être encodés dans un espace vectoriel compatible. Comparer des vecteurs provenant de deux modèles différents sans procédure appropriée n’a généralement pas de sens.

## 6.2 Similarité cosinus

Qdrant utilise la distance / similarité cosinus pour notre collection dense. L’idée : comparer la **direction** des vecteurs. Cela ne signifie pas que Qdrant comprend la vérité médicale ; il mesure une ressemblance dans l’espace appris par le modèle.

## 6.3 Identifier un point de façon stable

Dans `etl/index.py` :

```python
from uuid import uuid5, NAMESPACE_URL
point_id = str(uuid5(NAMESPACE_URL, record["chunk_id"]))
```

`uuid5` crée un identifiant **déterministe** : le même `chunk_id` donne le même UUID. Cela rend les mises à jour reproductibles et facilite la correspondance entre PostgreSQL et Qdrant.

À l’inverse, `uuid4()` produit un identifiant aléatoire : approprié pour une nouvelle exécution ETL, mais pas idéal pour identifier de manière reproductible le même chunk.

## 6.4 Indexation et vérifications

Le pipeline génère les embeddings, puis utilise `client.upsert(...)` pour insérer les points. `upsert` signifie « insérer ou mettre à jour » selon l’identifiant.

**Collection dense historique :** `hopital_bge_m3_512` avec **1 173 points**.

Le script `scripts/register_baseline.py` vérifie `280` documents, `1173` lignes JSONL et `1173` points Qdrant. Son propre commentaire précise que, dans ce snapshot, **les nombres ont été vérifiés, pas encore l’identité de chaque point individuellement**. C’est un exemple utile de validation honnête.

---

# 7. Trois méthodes de recherche : Dense, Sparse, Hybrid

## 7.1 Dense — recherche par similarité sémantique

La question passe au serveur d’embeddings BGE-M3. Son vecteur est comparé aux vecteurs stockés dans Qdrant :

```text
Question -> BGE-M3 -> vecteur dense -> Qdrant -> passages proches
```

Avantage : retrouver des formulations proches par le sens même si les mots diffèrent. Limites : confusion entre documents semblables, doses et identités, passage spécifique parfois mal classé.

Dans `rag/search.py`, l’appel dense ressemble à :

```python
vector = embed_texts([query])[0]
response = client.query_points(
    collection_name=COLLECTION,
    query=vector,
    limit=5,
    with_payload=True,
)
```

## 7.2 Sparse — recherche lexicale BM25

Sparse signifie **creux** : parmi un grand nombre de dimensions liées au vocabulaire, seules quelques-unes sont actives pour une expression donnée.

BM25 donne du poids aux termes selon leur fréquence locale, leur rareté dans le corpus et la longueur des documents. Les noms de médicament, noms de patient, abréviations et termes exacts peuvent être avantageux.

Exemple **illustratif** :

```text
"Le patient prend du ramipril 5 mg par jour"
-> indices de termes : [1796268431, 218297481, ...]
-> poids         : [1.6653, 1.6653, ...]
```

Lors du vrai test local, FastEmbed (`Qdrant/bm25`, `language="french"`) a produit **6 dimensions actives** pour cet exemple. L’avertissement relatif à Hugging Face n’a pas empêché le test : les ressources ont été récupérées puis réutilisées localement.

**Précision fondamentale :** BM25 n’« invente » pas un nombre absent de la requête. Il classe des documents en fonction des termes correspondants.

## 7.3 Hybrid — utiliser les deux classements

La collection `hopital_bge_m3_512_hybrid` contient deux vecteurs nommés :

- `dense` : BGE-M3, dimension 1 024 ;
- `bm25` : sparse, avec modificateur `IDF` côté Qdrant.

Elle contient **1 173 points**, copiés depuis la collection dense en réutilisant les vecteurs existants. Les seuls nouveaux vecteurs calculés étaient les sparse BM25. Aucune réindexation GPU dense n’a été nécessaire.

```text
                           Question
                          /        \
                         /          \
                  BGE-M3 dense    BM25 sparse
                       |              |
                   Top 30          Top 30
                         \          /
                          \        /
                     Fusion RRF
                           |
                        Top 5
```

Le **RRF — Reciprocal Rank Fusion** combine des positions dans plusieurs classements. Un passage bien placé dans les deux listes peut remonter. Les scores initiaux ne doivent **pas** être additionnés naïvement : cosine, BM25 et RRF n’ont pas la même échelle.

Formule pédagogique de RRF, pour une liste de classements :

**Formule :** `RRF(d) = somme de 1 / (k + rang(d)) sur les classements où d apparaît`.

La méthode est utilisée avec un paramètre de stabilisation `k`. Dans le notebook du professeur, **`k=60` est explicite**. Dans notre `search.py` actuel, l’appel utilise `models.FusionQuery(fusion=models.Fusion.RRF)` **sans inscrire explicitement cette même valeur**. Il faut donc distinguer les deux configurations et ne pas présenter l’expérience 6 comme copie exacte du notebook.

## 7.4 Test réel : Q001

Question : « Quelle était l’HbA1c de M. Jean Simon sur le bilan biologique d’avril 2025 ? »

Le passage nécessaire est `4100021_2025-04-11_bilan.docx`, **chunk 1**. La valeur attendue est **8,5 %**.

| Méthode | Position de la preuve principale | Lecture |
|---|---:|---|
| Dense | 3 | Preuve présente, mais deux chunks avant elle. |
| Sparse | **1** | Les termes exacts ont favorisé le bon passage. |
| Hybrid | **1** | La fusion conserve le bon classement pour ce cas. |

**Attention :** un exemple favorable ne démontre pas la supériorité sur tout le jeu. Le benchmark des 100 questions a montré une autre image.

## 7.5 Pourquoi Top 30 et Top 5 ?

`candidates=30` dans l’étape hybride signifie **30 candidats par branche** Dense et BM25 avant fusion. `top_k=5` signifie **cinq chunks finaux**.

Le pool de **30 chunks fusionnés** qui sera nécessaire pour le reranker en E11 **n’est pas encore la sortie de l’expérience 6** : celle-ci conserve uniquement les cinq meilleurs après RRF. Ce détail est crucial pour une comparaison expérimentale honnête.

---

# 8. Comprendre le jeu d’évaluation du professeur

## 8.1 Pourquoi 106 questions, mais 100 scores de retrieval ?

`hopital_eval.json` contient :

- **100 questions avec preuves de référence**, destinées à mesurer le retrieval ;
- **6 questions `out_of_corpus`**, sans réponse dans le corpus, destinées à mesurer la capacité du futur LLM à refuser une réponse injustifiée.

Les six questions ne sont pas forcément Q101–Q106 ; **on les exclut par leur champ `type`**, et non par leur numéro.

```python
selected_questions = [
    q for q in questions
    if q["type"] != "out_of_corpus"
]
assert len(selected_questions) == 100
```

Cette séparation est **prévue par l’énoncé**, pas une omission accidentelle.

## 8.2 Catégories de pièges

| Type | Nombre | Difficulté |
|---|---:|---|
| `dose` | 8 | Dose précise, patient et date. |
| `table` | 8 | Valeur dans un tableau. |
| `imaging` | 5 | Compte rendu PDF d’imagerie. |
| `abbreviation` | 8 | Sigle dans le document, formulation longue dans la question. |
| `lay_language` | 8 | Langage courant vs vocabulaire médical. |
| `buried` | 8 | Information enfouie. |
| `split` | 8 | Information répartie sur plusieurs passages. |
| `negation` | 8 | Négation à conserver. |
| `temporal` | 8 | Information la plus récente. |
| `drug_info` | 5 | Notice de médicament. |
| `multi_hop` | 12 | Plusieurs faits provenant de plusieurs sources. |
| `cross_patient` | 8 | Plusieurs patients, éviter les confusions. |
| `cross_notice` | 6 | Plusieurs notices de médicaments. |
| `out_of_corpus` | 6 | Refus si preuve absente. |

## 8.3 `evidence`, `grade` et `fact`

Exemple **adapté du format de l’énoncé** :

```json
{
  "id": "Q007",
  "type": "dose",
  "question": "Quelle dose de ramipril prend M. Bruno Martin ?",
  "evidence": [
    {"document": "...ordonnance.docx", "snippets": ["Ramipril 5 mg"], "grade": 2, "fact": 0},
    {"document": "...consultation.docx", "snippets": ["ramipril 5 mg par jour"], "grade": 2, "fact": 0},
    {"document": "...autre_consultation.docx", "snippets": ["à 5 mg par jour"], "grade": 1, "fact": null}
  ]
}
```

- `grade=2` : preuve contenant un fait nécessaire.
- `grade=1` : preuve utile, mais insuffisante à elle seule.
- `grade=0` : aucune preuve de référence reconnue dans le chunk.
- `fact=0`, `fact=1`, etc. : identifiants des faits requis.
- **Même numéro `fact`** : sources **interchangeables** fournissant un même fait.
- **Numéros différents** : faits complémentaires, tous nécessaires.
- `fact=null` : pas un fait requis. **`fact=0` n’est pas `null`.**

### Pourquoi `fact=0` est un piège Python

```python
if evidence["fact"]:              # MAUVAIS : 0 est évalué comme False
    ...

if evidence["fact"] is not None:  # CORRECT : 0 est un identifiant valide
    ...
```

## 8.4 Reconnaître une preuve

Notre `judge_chunk(question, document, text)` vérifie :

1. que le nom du document correspond à celui d’une preuve du référentiel ;
2. que tous les extraits (`snippets`) attendus sont présents dans le texte, avec comparaison insensible à la casse.

Ce jugement est **déterministe** : il ne fait pas appel à un modèle de langage. Il peut manquer une preuve reformulée, car il s’appuie sur des sous-chaînes précises. C’est un choix méthodologique à connaître.

---

# 9. Les métriques — ce qu’elles mesurent réellement

**Toujours préciser ce que représente le chiffre.** Nous ne mesurons pas encore l’exactitude d’une réponse rédigée par LLM.

## 9.1 `full_answer_hit@5` : tous les faits sont-ils trouvés ?

Résultat **binaire par question** :

- `1` : tous les faits nécessaires apparaissent dans les cinq premiers chunks ;
- `0` : il manque au moins un fait.

Exemple : une question nécessite **trois** faits, le retrieval en trouve **deux** ; `full_answer_hit@5 = 0`.

Sur 100 questions, moyenne `0.77` = **77 questions complètes**, selon notre système de reconnaissance des preuves.

**Différence avec le cours :** l’exemple de Hit@k du notebook `06_evaluation.ipynb` cherche **au moins un** chunk attendu. Ce n’est **pas** identique à notre `full_answer_hit@5`, plus strict pour les questions multi-faits.

## 9.2 `fact_recall@5` : quelle proportion des faits requis ?

**Formule :** `Fact Recall@5 = faits nécessaires distincts trouvés / faits nécessaires distincts attendus`.

Exemple : **2** faits sur **4** -> `0.50`. Le recall reconnaît donc les réponses **partiellement étayées**, contrairement au Hit complet.

## 9.3 `full_answer_rr@5` : à quel rang la couverture devient-elle complète ?

Si la couverture devient complète au rang `r`, la valeur est `1/r` ; sinon `0`.

- Complète au rang 1 -> `1.0000`.
- Complète au rang 3 -> `0.3333`.
- Jamais complète dans les cinq -> `0`.

Pour une question `multi_hop`, cette métrique attend l’instant où **tous les faits** ont été trouvés ; elle ne se limite pas au premier chunk pertinent.

## 9.4 `ndcg@5` : les preuves sont-elles bien classées ?

**nDCG — Normalized Discounted Cumulative Gain** : les grades comptent davantage quand les documents sont près du rang 1. Le facteur de rang utilise le logarithme en base 2.

**Formules :** `DCG@5 = somme [grade au rang r / log2(r + 1)] pour r=1..5` ; `nDCG@5 = DCG@5 / IDCG@5`.

`IDCG` est le meilleur score possible selon la convention de pertinence choisie. La valeur doit se situer entre **0** et **1** si la normalisation est cohérente.

### Exemple réel : Q003

```text
Dense  : grades [0, 0, 2, 0, 0] -> nDCG@5 = 0,5000
Sparse : grades [2, 0, 0, 0, 0] -> nDCG@5 = 1,0000
```

Les deux méthodes retrouvent la preuve, mais **Sparse** la place immédiatement au premier rang.

### Le bug Q041 et la correction

Pour Q041 (`temporal`), les preuves de référence avaient les grades `[2, 1, 1]`, mais les chunks retrouvés donnaient `[2, 1, 1, 1, 0]`. Le calcul initial comptait la même preuve plusieurs fois et renvoyait **`1.1376`**, ce qui est invalide pour un nDCG normalisé.

Nous avons corrigé `evaluation/runner.py` : une **preuve de référence distincte** ne contribue qu’à sa première apparition dans le classement. Résultat vérifié : **Q041 = `0.9779`**, maximum de la série `1.0`, **0 scores invalides**.

**Limite à documenter :** ce nDCG est une **variante fondée sur les preuves distinctes**, différente du nDCG classique par chunk du notebook du professeur. Il est comparable **en interne** si la convention reste identique pour toutes nos expériences, mais il ne faut pas le publier comme nDCG standard sans préciser sa définition.

## 9.5 Résumé : lire les chiffres ensemble

| Situation | Hit complet | Recall | nDCG | Diagnostic |
|---|---:|---:|---:|---|
| Tous les faits, bien classés | 1 | 1 | Élevé | Retrieval de bonne qualité. |
| Tous les faits, trop bas | 1 | 1 | Plus faible | Classement à améliorer. |
| Seulement une partie des faits | 0 | Entre 0 et 1 | Variable | Problème de couverture. |
| Aucune preuve reconnue | 0 | 0 | 0 | Échec d’identification ou de retrieval. |

---

# 10. PostgreSQL : conserver les expériences plutôt que les oublier

## 10.1 Trois tables principales

```text
experiments (UNE ligne par expérience)
  id | name | config (JSONB) | duration_s | status
       │
       ├────────► answers (UNE ligne par question et expérience)
       │             question_id | chunks (JSONB) | latency_ms | answer
       │
       └────────► scores (UNE ligne par métrique et question)
                     question_id | metric | value | reason
```

`experiments.config` conserve les paramètres. `answers.chunks` conserve les identifiants, positions, documents et scores des chunks retrouvés. `scores` conserve les résultats de l’évaluation.

Pour 100 questions et **6 métriques par question**, une expérience complète produit **600 lignes** de scores.

## 10.2 Notion de clé primaire composée

Dans `scores`, la clé est :

```sql
PRIMARY KEY (experiment_id, question_id, metric)
```

Cela signifie que la même métrique pour la même question dans la même expérience n’existe qu’une fois. `ON CONFLICT ... DO UPDATE` permet de **recalculer** les scores sans créer de doublons ni refaire le retrieval.

## 10.3 Pourquoi retrouver les chunks dans Qdrant ?

PostgreSQL stocke une liste JSON de chunks avec leur `chunk_id` ; le calculateur utilise cet identifiant pour reconstruire l’UUID et récupérer le **texte d’origine** depuis Qdrant. `runner.py` peut ensuite comparer ce texte aux preuves du professeur.

Cette évaluation **ne lance pas une nouvelle recherche sémantique**. Elle relit les résultats sauvegardés : c’est pourquoi nous avons corrigé Q041 sans refaire les 100 requêtes de retrieval.

## 10.4 Bash n’est pas SQL — une erreur réellement rencontrée

Coller directement `SELECT`, `FROM`, `WHERE` au prompt Bash produit `command not found`. Le SQL doit être exécuté **par `psql`**, par exemple :

```bash
docker compose exec -T postgres psql -U coursrag -d rag_hopital <<'SQL'
SELECT id, name, status FROM experiments ORDER BY id;
SQL
```

Le marqueur final `SQL` doit être seul sur sa ligne. `<<'SQL'` est un **here-document Bash** : le bloc suivant est envoyé à l’entrée standard de `psql`.

### Requête utile : comparaison des trois expériences

```sql
SELECT
    e.id,
    e.name,
    COUNT(DISTINCT s.question_id) AS questions,
    ROUND(AVG(s.value) FILTER (WHERE s.metric='full_answer_hit@5')::numeric, 4) AS hit_5,
    ROUND(AVG(s.value) FILTER (WHERE s.metric='fact_recall@5')::numeric, 4) AS recall_5,
    ROUND(AVG(s.value) FILTER (WHERE s.metric='ndcg@5')::numeric, 4) AS ndcg_5
FROM experiments e
JOIN scores s ON s.experiment_id=e.id
WHERE e.id IN (3, 5, 6)
GROUP BY e.id, e.name
ORDER BY e.id;
```

**Comment lire SQL :** `JOIN` relie les tables, `WHERE` sélectionne les expériences, `GROUP BY` rassemble les lignes, `AVG` calcule la moyenne, `FILTER` choisit la métrique concernée.

---

# 11. TOML : rendre les expériences reproductibles

## 11.1 Le rôle d’un fichier TOML

TOML est du **texte de configuration**, différent du **code Python** :

- Python dit **comment** chercher et enregistrer les résultats.
- TOML dit **avec quels paramètres** lancer une expérience.
- PostgreSQL dit **ce qui a été exécuté** et **ce que cela a donné**.

Extrait de notre `experiments/hybrid_bge_bm25.toml` :

```toml
name = "hybrid_bge_bm25_100_v1"
dataset = "hopital_eval.json"

[chunking]
max_tokens = 512
patient_line = true
overlap = 0

[embedder]
model = "bge-m3"

[search]
method = "hybrid"
collection = "hopital_bge_m3_512_hybrid"
sparse_model = "Qdrant/bm25"
sparse_language = "french"
fusion = "rrf"
top_k = 5
candidates = 30
```

**Exercice d’observation :** que se passerait-il si on écrivait `parse_model` à la place de `sparse_model` ? Notre validateur refuserait la configuration sparse actuelle. L’extrait reste partiel : le fichier opérationnel comporte aussi les sections `[reranker]` et `[generation]`.

Dans TOML, `"hybrid"` est une chaîne (`str`), `30` est un entier (`int`), `true`/`false` sont des booléens. Les sections `[search]` et `[embedder]` deviennent des dictionnaires imbriqués en Python.

## 11.2 Lire le TOML en Python

```python
import tomllib
from pathlib import Path

path = Path("experiments/hybrid_bge_bm25.toml")
with path.open("rb") as file:
    config = tomllib.load(file)

print(config["search"]["method"])      # hybrid
print(config["search"]["candidates"])  # 30
```

## 11.3 Les trois modes du script

Depuis `~/formation/RAG/rag-hopital` :

```bash
# Vérifier les paramètres ; ne crée pas de nouvelle expérience.
uv run python scripts/run_experiment.py experiments/hybrid_bge_bm25.toml --check-config

# Lancer 3 questions ; crée UNE expérience PostgreSQL distincte.
uv run python scripts/run_experiment.py experiments/hybrid_bge_bm25.toml --limit 3

# Réévaluer une expérience existante ; ne relance pas le retrieval.
uv run python scripts/run_experiment.py --evaluate-existing 6
```

**Ne pas réexécuter sans nécessité une commande d’expérience normale** : elle crée un nouvel ID PostgreSQL. **Ne jamais supposer un ID** : il faut lire l’ID réellement renvoyé.

## 11.4 Ce que notre validation TOML sait refuser

Notre script valide actuellement : type de recherche, 512 tokens, ligne patient, overlap explicite à 0, BGE-M3, top 5, collections correctes, BM25 français et fusion RRF. Il refuse les alternatives non implémentées : autre embedder, reranker actif, génération LLM. C’est préférable à accepter silencieusement une configuration que le code ne sait pas honorer.

**Attention :** la configuration indique les éléments expérimentaux ; elle ne garantit pas à elle seule que **tous** les paramètres d’exécution effectifs (par exemple le `k` du RRF) sont explicitement renseignés. L’audit de reproductibilité reste nécessaire.

---

# 12. Lire les vrais résultats et éviter les conclusions hâtives

## 12.1 Trois expériences sur exactement 100 questions

| Expérience | Méthode | Full-answer Hit@5 | Fact Recall@5 | nDCG@5* | Durée du run de retrieval |
|---|---|---:|---:|---:|---:|
| **3** | Dense BGE-M3 | **0,7700** | 0,8290 | 0,6705 | 3,89 s |
| **5** | Sparse BM25 | 0,6900 | 0,7377 | 0,6247 | 3,39 s |
| **6** | Hybrid RRF | **0,7700** | **0,8377** | **0,6955** | 4,49 s |

\* nDCG@5 avec notre convention de preuves distinctes. Les durées sont les temps mesurés **pour ces exécutions**, pas des benchmarks reproductibles de débit ou de latence froide/chaude.

## 12.2 Conclusions défendables

- **Dense** trouve tous les faits nécessaires pour **77 questions** sur 100.
- **Sparse** fait moins bien globalement : **69 questions** complètes, malgré un bon classement sur Q001 et Q003.
- **Hybrid** ne change pas le nombre de questions complètes (**77**) mais améliore légèrement **Fact Recall@5** (+0,0087) et **nDCG@5** (+0,0250) par rapport à Dense.
- **Hybrid** est le meilleur compromis **provisoire** dans les mesures produites, mais il coûte un peu plus de temps à cette exécution.

**Mauvaise conclusion :** « Hybrid répond à toutes les questions » ou « BM25 est toujours moins bon ». Les résultats portent sur ce corpus, cette configuration et ces définitions de métriques.

## 12.3 Ce que signifie « même Hit@5 »

Nous avons comparé question par question les expériences 3 et 6 : **4 questions améliorées, 4 régressées**, 92 au même état pour `full_answer_hit@5`.

| Type | Améliorées | Régressées |
|---|---:|---:|
| `abbreviation` | 1 | 1 |
| `cross_patient` | 0 | 1 |
| `imaging` | 1 | 0 |
| `lay_language` | 0 | 1 |
| `multi_hop` | 1 | 1 |
| `negation` | 1 | 0 |
| Autres catégories | 0 | 0 |
| **Total** | **4** | **4** |

Deux méthodes avec la **même moyenne** peuvent échouer sur des **questions différentes**. C’est pourquoi il faut analyser les catégories et les cas d’erreur, pas seulement les moyennes.

## 12.4 La question des causes

Une question ratée peut provenir de plusieurs causes :

- conversion Docling incomplète ;
- mauvaise fragmentation du texte ;
- absence de ligne patient exploitable ;
- limites lexicales ou sémantiques de l’embedder ;
- seulement 5 passages conservés ;
- besoin de nombreux documents (`cross_notice`, `multi_hop`) ;
- reconnaissance déterministe trop stricte des `snippets`.

Il faut **localiser la cause** avant de choisir une optimisation. Un reranker ne peut pas retrouver un fait absent de son pool de candidats.

---

# 13. Les erreurs que nous avons réellement corrigées

## 13.1 Coller du SQL dans Bash

**Symptôme :** `SELECT: command not found`, `syntax error near '('`.  
**Cause :** la commande était interprétée par le shell Linux.  
**Correction :** utiliser `docker compose exec ... psql` ou un here-document `<<'SQL'`.

## 13.2 `.gitignore` sans effet apparent

**Symptôme :** `git check-ignore` n’affichait rien ; `.gitignore` ne figurait pas dans le staging.  
**Cause vérifiée :** les nouvelles lignes n’avaient pas été réellement enregistrées dans le `.gitignore` racine.  
**Correction :** ajouter les deux exclusions, puis `git check-ignore -v --no-index ...` ; lignes 59 et 60 confirmées.

## 13.3 Les fichiers générés suivis par Git

**Symptôme :** deux résultats générés figuraient dans le dépôt.  
**Correction :** `git rm --cached` puis règles `.gitignore`.  
**Leçon :** *retirer du suivi Git* ne signifie pas *effacer le fichier local*.

## 13.4 `NameError: matches is not defined`

**Symptôme :** échec d’import `runner.py`, ligne `for evidence in matches`.  
**Cause :** code mal indenté, boucle en dehors de la fonction / du bon bloc.  
**Correction :** remettre le calcul des grades dans la boucle des chunks, après l’appel à `judge_chunk()`.  
**Leçon Python :** l’indentation **détermine la portée et l’exécution**.

Lancer seulement `py_compile` vérifie la syntaxe, mais **n’exécute pas** le module : un `NameError` à l’import peut rester invisible. Tester également :

```bash
uv run python -c "from rag_hopital.evaluation.runner import evaluate_saved_experiment; print('IMPORT OK')"
```

## 13.5 Le nDCG supérieur à 1

**Symptôme :** Q041 = `1.1376`.  
**Cause :** preuves comptées plusieurs fois malgré un idéal fondé sur des preuves uniques.  
**Correction :** attribuer les grades selon la première apparition de chaque preuve de référence.  
**Contrôle :** Q041 = `0.9779`, maximum global `1`, `invalid_scores = 0`.

## 13.6 Copier tous les logs dans la conversation

**Symptôme :** résultats trop longs, difficiles à comparer.  
**Correction :** enregistrer les sorties longues dans `/tmp/*.log` puis ne montrer que `tail -n 5`, l’ID d’expérience et les **requêtes SQL synthétiques**.  
**Leçon :** utiliser la base de données comme source structurée, et non la conversation comme stockage de logs.

## 13.7 Télécharger avant d’inventorier

**Symptôme :** proposition d’installer / télécharger des modèles alors que la station en contient déjà plusieurs.  
**Correction de méthode :** **inventorier -> réutiliser -> vérifier compatibilité -> installer si nécessaire**. La machine possède déjà BGE-M3, BGE-Reranker-v2-M3, Qwen3-Embedding-0.6B et Qwen3-Reranker-0.6B. L’installation du modèle ne prouve pas qu’un service d’inférence est démarré.

---

# 14. Exercices d’autonomie (sans création de nouvelles expériences)

**Règle :** ces exercices sont en lecture seule ou utilisent des calculs locaux. Ils ne modifient pas les résultats des expériences 3, 5 et 6.

## Exercice A — Identifier l’environnement (5 min)

Sans regarder le manuel, expliquer la différence entre :

1. `uv run python` et `python` ;
2. `qdrant-client` et le serveur Qdrant ;
3. `uv.lock` et `.env` ;
4. `git push` et une sauvegarde PostgreSQL.

## Exercice B — Lire une structure Python imbriquée (10 min)

Considérer :

```python
question = {
    "id": "Q007",
    "type": "dose",
    "evidence": [
        {"grade": 2, "fact": 0},
        {"grade": 1, "fact": None},
    ],
}
```

Sans exécuter Python, donner le résultat de :

```python
question["id"]
question["evidence"][0]["grade"]
question["evidence"][0]["fact"] is not None
len(question["evidence"])
```

## Exercice C — Comprendre `enumerate()` (10 min)

Pourquoi utiliser `enumerate(points, start=1)` pour les résultats de recherche ? Que change `start=0` ?

## Exercice D — Calculer deux métriques (10 min)

Une question nécessite les faits `{0, 1, 2}`. Dans le Top 5, nous retrouvons `{0, 2}`. Calculer :

- Full-answer Hit@5 ;
- Fact Recall@5.

## Exercice E — Éviter les expériences inutiles (5 min)

Classer ces commandes : **lecture seule**, **nouvelle expérience**, **réévaluation**.

```bash
uv run python scripts/run_experiment.py experiments/hybrid_bge_bm25.toml --check-config
uv run python scripts/run_experiment.py experiments/hybrid_bge_bm25.toml --limit 3
uv run python scripts/run_experiment.py --evaluate-existing 6
```

## Exercice F — Lire une requête SQL (10 min)

Dans :

```sql
SELECT question_type, AVG(value)
FROM scores
WHERE experiment_id = 6 AND metric = 'fact_recall@5'
GROUP BY question_type;
```

Que représentent `WHERE`, `GROUP BY` et `AVG` ? La requête crée-t-elle de nouvelles données ?

## Exercice G — Vérifier une hypothèse expérimentale (10 min)

Hypothèse : « Hybrid est meilleur que Dense sur toutes les questions. »  
Quelles observations de nos expériences **réfutent** cette affirmation ?

## Exercice H — Préparer le raisonnement E11, sans coder (10 min)

Quelle différence entre :

- le **nombre de candidats** avant un reranker ;
- le **nombre de chunks final** envoyé au LLM ?

Pourquoi un reranker appliqué à seulement cinq candidats ne peut-il pas retrouver une preuve classée sixième ?

---

# 15. Grille d’évaluation personnelle : niveau réel, pas exposition au cours

Utiliser les colonnes suivantes après **démonstration personnelle**, pas simplement après lecture.

| Compétence | Test pour le niveau « autonome » | Niveau à noter |
|---|---|---|
| Terminal / répertoires | Se déplacer, trouver la racine Git, lire un log sans aide. | Vu / Guidé / Autonome / Prouvé |
| Python : listes, dictionnaires | Extraire les champs d’une question et parcourir les preuves. | Idem |
| Python : fonctions | Expliquer paramètres, retour, portée et indentation. | Idem |
| JSON / JSONL / TOML | Lire un exemple de chaque format et distinguer leurs rôles. | Idem |
| Docling / chunks | Expliquer pourquoi on préserve tableaux et ligne patient. | Idem |
| Qdrant | Distinguer collection, point, payload, dense, sparse. | Idem |
| Recherche | Décrire Dense, BM25, RRF et interpréter Top 5. | Idem |
| Évaluation | Calculer Hit complet et Fact Recall manuellement. | Idem |
| PostgreSQL | Lire les tables et exécuter un `SELECT` via `psql`. | Idem |
| Git | Stager uniquement le travail pertinent et vérifier `origin/main`. | Idem |
| Expérimentation | Expliquer la nécessité de « un seul changement à la fois ». | Idem |

**Point d’attention :** être capable d’expliquer **pourquoi** le code fonctionne est un niveau supérieur au simple fait d’obtenir `EXIT_CODE=0`.

---

# 16. Ce qui reste hors de la Partie I

## 16.1 Exigences importantes non encore réalisées

- **E11 :** BGE-Reranker-v2-M3 sur un pool de candidats, puis comparaison avec le même pool sans reranker.
- Sélection de modèles alternatifs (embedders et rerankers) sans recopier l’application.
- Génération de réponses par LLM à partir des chunks.
- Évaluation des réponses et de la fidélité avec un juge LLM, selon le cours.
- Évaluation des **6 questions `out_of_corpus`** pour les refus.
- Expériences sur tailles des chunks, overlap, filtres, prompts et paramètres du LLM.
- Au moins deux autres pistes d’optimisation prévues par l’énoncé.
- `RAPPORT.md` avec comparaison, meilleur compromis et trois échecs analysés.

## 16.2 Précautions avant de revendiquer la « configuration de référence »

1. Dans le notebook de démonstration du professeur, RRF indique `k=60` ; notre appel Qdrant actuel n’écrit pas ce nombre explicitement.
2. Notre BM25 FastEmbed français n’utilise pas exactement la même interface et les mêmes options affichées dans son notebook.
3. Nos métriques `full_answer_hit@5` et nDCG à preuves distinctes diffèrent de certaines définitions de son notebook d’introduction.
4. La configuration de référence de l’exercice inclut **hybrid + reranker BGE** : **pas encore terminée** à E10.

Ces écarts ne rendent pas nos expérimentations inutiles. Ils doivent être **connus et documentés** pour que les comparaisons restent valides.

---

# 17. Glossaire compact français–anglais

| Terme | Sens pratique |
|---|---|
| RAG | Retrieval-Augmented Generation ; retrieval puis génération appuyée sur des preuves. |
| Corpus | Ensemble de documents utilisés comme sources. |
| ETL | Extraction, transformation et chargement des données. |
| OCR | Reconnaissance de texte dans des images ou PDF scannés. |
| Token | Unité de texte traitée par un tokenizer ; pas nécessairement un mot entier. |
| Chunk | Fragment de document indexé séparément. |
| Payload | Métadonnées associées à un point Qdrant. |
| Embedding | Représentation vectorielle numérique d’un texte. |
| Dense | Vecteur avec beaucoup de composantes actives ; recherche sémantique. |
| Sparse | Vecteur creux ; ici recherche lexicale BM25. |
| BM25 | Algorithme de classement fondé sur les termes et leurs statistiques. |
| IDF | Inverse Document Frequency ; importance liée à la rareté d’un terme. |
| Hybrid | Combinaison de plusieurs méthodes de retrieval. |
| RRF | Reciprocal Rank Fusion ; fusion de classements par les positions. |
| Top-k | Nombre de résultats retenus ; ici k=5 pour les métriques finales. |
| Golden dataset | Questions et preuves de référence pour l’évaluation. |
| Evidence / preuve | Source et extrait attendu dans le corpus. |
| Grade | Degré de pertinence d’une preuve reconnue. |
| Fact | Identifiant d’un fait requis ; mêmes numéros = sources interchangeables. |
| Hit@k | Présence de preuve(s) dans les k premiers résultats ; **définition à préciser**. |
| Recall@k | Proportion des éléments attendus retrouvés dans les k premiers résultats. |
| nDCG@k | Qualité du classement pondérée par les grades et les positions. |
| Reranker | Modèle qui réordonne des candidats déjà retrouvés. |
| TOML | Fichier texte de paramètres expérimentaux. |
| JSONL | Un objet JSON par ligne. |
| JSONB | Type PostgreSQL pour stocker et interroger du JSON. |
| Upsert | Insérer ou mettre à jour selon une clé existante. |
| Reproductibilité | Pouvoir relancer une expérience en connaissant ses paramètres et données. |

---

# 18. Corrigé des exercices — à consulter après l’essai

**B.** `"Q007"` ; `2` ; `True` ; `2`.

**C.** `enumerate(points, start=1)` associe chaque résultat à un rang lisible 1, 2, 3... ; `start=0` donnerait des indices commençant par 0. Le rang d’un résultat n’est pas son identifiant.

**D.** Hit complet = `0`, car il manque le fait `1` ; Fact Recall = `2/3`, environ `0.6667`.

**E.** Première commande : lecture / validation seule ; deuxième : nouvelle expérience PostgreSQL ; troisième : réévaluation des résultats existants.

**F.** `WHERE` filtre les lignes ; `GROUP BY` rassemble par `question_type` ; `AVG` calcule la moyenne des scores ; `SELECT` ne modifie pas la base.

**G.** Hybrid a **quatre régressions** par rapport à Dense ; ses **77 succès complets** ne sont donc pas exactement les mêmes que ceux de Dense. L’hypothèse « meilleur partout » est fausse.

**H.** Le pool de candidats est l’ensemble que le reranker peut réordonner ; le Top 5 final est le sous-ensemble transmis ensuite. Une preuve absente des cinq candidats ne peut pas être récupérée par leur simple réordonnancement.

**A.** Voir chapitre 4 : Python actif, bibliothèque vs serveur, versions vs secrets, code Git vs volumes de données.

---

# 19. Fiche de reprise en une page — fin E10 / début E11

**Dossier local :** `~/formation/RAG/rag-hopital`  
**Dépôt :** `Mircea11/BF_IntegIA_2026`  
**Commit sauvegardé :** `1369025`  
**Collections Qdrant :** `hopital_bge_m3_512` et `hopital_bge_m3_512_hybrid` ; **1 173 points chacune**.  
**Expériences clés PostgreSQL :** `3` Dense / `5` Sparse / `6` Hybrid ; **100 questions évaluées dans chacune**.  
**Dernier constat :** Hybrid Hit complet 77 %, Fact Recall 83,77 %, nDCG 0,6955 (convention interne).  
**Modèle reranker déjà sur la machine :** `~/models/rag/reranker/bge-reranker-v2-m3`.  
**Prochaine action pratique :** vérifier son environnement / serveur avant intégration ; ne pas télécharger à nouveau les modèles déjà présents.  
**Règle de comparaison :** garder le même pool de candidats lorsqu’on mesure l’effet **du reranker seul**.  
**Sécurité :** ne pas lancer `docker compose down -v` sans intention de supprimer les volumes ; pas de secrets `.env` dans Git.  
**Version documentaire :** Partie I figée à E10 ; **Partie II commencera à E11**.

## Références dans le dépôt

- `RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/demo/exercice_03_recap_enonce.md` — consignes et critères de l’exercice.
- `.../demo/04_intro_qdrant.ipynb` — dense, sparse, hybride et RRF dans le cours.
- `.../demo/05_advanced_filtering_and_reranker.ipynb` — démonstration de filtrage et de reranking.
- `.../demo/06_evaluation.ipynb` — métriques classiques et introduction au juge LLM.
- `RAG/rag-hopital/src/rag_hopital/` — notre logique Python ; `RAG/rag-hopital/experiments/` — nos configurations.

**Fin de la Partie I — E01 à E10.**

# Partie II — E11 à E15 : Recherche, génération et évaluation

## E11 — Recherche documentaire

Objectif : retrouver les passages pertinents avant de générer une réponse.

Architecture :
- BGE-M3 pour les embeddings.
- BM25 pour la recherche lexicale.
- Fusion RRF pour la recherche hybride.
- BGE-reranker-v2-m3 pour reclasser les candidats.
- Qdrant pour conserver les vecteurs et les passages.

Résultats sur 100 questions :
- Hit@5 : 77 % sans reranking, 88 % avec reranking.
- Fact Recall@5 : 83,77 % puis 92,63 %.
- nDCG@5 : 69,55 % puis 80,89 %.

Leçon : retrouver le bon document ne garantit pas de retrouver le bon passage.

## E12 — Génération RAG

Modèle : Qwen 3.5 9B via vLLM.

Pipeline :
Question → recherche hybride → reranking → cinq passages → prompt → réponse citée.

Résultats :
- 106 questions traitées.
- Expérience PostgreSQL ID 12.
- Latence moyenne : 15,93 secondes.
- Refus hors corpus corrects : 5/6.

Les réponses et les passages associés ont été sauvegardés pour permettre
leur évaluation sans relancer la génération.

## E13 — Amélioration du prompt

Une règle 11 interdit d'inférer l'absence d'un médicament ou d'une
posologie simplement parce que les passages ne les mentionnent pas.

Le baseline à dix règles a été conservé.
La version V2 à onze règles est configurée mais non réévaluée.

Leçon : une consigne plus précise peut réduire certains risques,
mais son effet réel doit être distingué d'une amélioration mesurée.

## E14 — LLM-as-Judge

Générateur : Qwen 3.5 9B.
Juge indépendant du générateur : Granite 4.1 8B.

Échantillon : 26 questions, deux dans chacune des 13 catégories répondables.

Résultats :
- Exactitude moyenne : 92,3 %.
- Complétude moyenne : 80,8 %.
- Réponses jugées exactes : 24/26.
- Réponses jugées complètes : 18/26.
- Erreurs détectées : Q011 et Q089.

Limite : le juge compare les réponses aux références.
Il ne prouve pas que les citations correspondent aux documents.

## E15 — Analyse des erreurs et documentation

Q045 : inférence injustifiée concernant la metformine.
Correction proposée : règle 11.

Q063 : le bon document d'imagerie a été identifié, mais le chunk
contenant « insuffisance mitrale modérée » n'a pas été sélectionné.

Q089 : preuves documentaires incomplètes pour une question
sur l'association ramipril–sacubitril/valsartan.

Q011 : refus de fournir une valeur numérique présente
dans la réponse de référence.

Livrables :
- README.md : présentation du projet et résultats.
- RAPPORT.md : méthodologie, métriques et analyses d'erreurs.
- reports/ : réponses, échantillon et évaluations.
- experiments/ : configurations reproductibles.
- prompts/ : baseline et version V2.

## Compétences à consolider

- Expliquer la différence entre recherche dense, BM25 et reranking.
- Comprendre le calcul des métriques retrieval.
- Diagnostiquer un mauvais passage dans Qdrant.
- Suivre une réponse depuis les sources jusqu'à PostgreSQL.
- Exécuter et interpréter une évaluation LLM-as-Judge.
- Distinguer résultat observé, hypothèse et amélioration démontrée.

Ce projet utilise des documents médicaux fictifs.
Il ne constitue pas un dispositif médical.
