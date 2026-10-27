# Cours personnel 14 — RAG : extraction, Docling, chunking et embeddings

**AI Integration Specialist · Consolidation personnelle · 26 octobre 2026**  
**Période du support :** 2–9 octobre 2026 ; prolongements de tes travaux vérifiés : 12–15 octobre.  
**Support du collègue :** `2026-10-02_09 - RAG, extraction et chunking (Docling).md`, dans `2026 Cours.zip`. Synthèse du module de Romain Wauman ; le document indique lui-même qu'il est reconstruit à partir des fichiers du cours, sans notes manuscrites.  
**Sources du professeur vérifiées :** `demo/00_setup.md`, `demo/01_intro.ipynb`, `demo/02_intro_docling.ipynb` du dépôt de formation.  
**Traces de tes travaux :** notebooks datés du 12, 14 et 15 octobre, exercice ETL corrigé, notebooks `demo_chunking_embedding.ipynb`, et projet B5.  
**Lecture :** 75–100 min. **Pratique :** trois blocs de 45 min, en lecture seule ou sur exemples isolés.

> **Règle de preuve.** Un notebook présent sur GitHub prouve l'existence d'un fichier et de son code. Des cellules avec sorties indiquent une exécution enregistrée, sans prouver que tu peux reconstruire le programme seul. Une compétence est **autonome** lorsqu'elle est exécutée, expliquée et contrôlée sans mon aide. Les résultats des serveurs et bases sur ton Z4 doivent être recontrôlés localement.

## 1. Où ce cours se place dans ta formation

Tu connais déjà plusieurs pièces : Python (cours 02/06), PostgreSQL (03/04), API (07), Polars (08), LLM (09), vLLM (12) et Docker (13). **Le RAG relie ces outils pour répondre à partir d'une collection de documents.** Son intérêt professionnel vient de la chaîne de traçabilité : documents reçus → extraction vérifiée → recherche pertinente → réponse justifiée.

**Deux phases distinctes :**

```text
PHASE A — INGESTION (lorsque les documents changent)
PDF / DOCX / PPTX / HTML
    → Docling ou autre extracteur → DoclingDocument → JSON structuré
    → chunks + métadonnées → BGE-M3 → vecteurs + texte → Qdrant
    └── journal PostgreSQL : exécution, empreinte, statut, erreurs

PHASE B — QUESTION (à chaque question)
Question → BGE-M3 → recherche Qdrant (dense, parfois sparse/hybride)
         → passages + source/page → prompt → Nemotron → réponse
                                          └→ contrôle de sources et refus si preuve insuffisante
```

**Analogie métier :** le RAG est une procédure de sélection des pièces pertinentes avant de rédiger une note. L'extracteur prépare les documents, le système de recherche choisit des passages et le LLM rédige. Le RAG ne réentraîne pas les poids du LLM : il lui apporte des éléments de contexte au moment de répondre.

| Élément | À quoi il sert | Référence dans tes projets |
|---|---|---|
| Docling | Transformer des fichiers difficiles en structure exploitable | Démo du professeur ; notebook ETL |
| PostgreSQL | Journal d'exécution et contrôle de traitement | `schema.sql`, exercice ETL |
| HybridChunker | Découper sans perdre les titres et limites de tokens | Notebook `demo_chunking_embedding.ipynb` |
| BGE-M3 | Produire des vecteurs multilingues | Port 8001 du Z4 selon configuration documentée |
| Qdrant | Trouver les passages par proximité | Notebook du 14/10 ; B5 |
| Nemotron | Générer une réponse à partir des passages | Notebook du 15/10 ; B5 |

## 2. Commencer par les documents : le corpus Veltis

Le cours travaille sur **Veltis**, une société fictive. Les supports combinent PDF, procès-verbal numérisé, DOCX, PPTX et HTML. Les documents n'ont pas la même structure et ne demandent pas tous le même extracteur.

### 2.1 Extraction brute avec PyMuPDF

```python
from pathlib import Path
import pymupdf

source = Path("data/veltis/rapport_annuel_2025.pdf")
with pymupdf.open(source) as pdf:
    page = pdf[0]
    texte = page.get_text()
    blocs = page.get_text("dict")
    print("Caractères de la page 1 :", len(texte))
    print("Blocs trouvés :", len(blocs.get("blocks", [])))
```

Ce code **illustre** la démarche du professeur ; le chemin est relatif au dossier `demo` contenant le corpus. À vérifier sur ton Z4 avant exécution. Ne le copie pas depuis le dossier racine du dépôt en supposant que les chemins fonctionneront.

**Limites observées dans les démonstrations :** en-têtes répétés, ordre de lecture incertain, titres non reconnus, tableaux fragmentés, colonnes mélangées et PDF numérisé sans couche texte. Dans un PDF scanné, `get_text()` peut ne rien retourner d'utile. Une image ou un graphique vectoriel n'est pas un paragraphe textuel ; il faut une stratégie adaptée, éventuellement OCR ou modèle vision.

### 2.2 Ce que Docling ajoute

Docling convertit le document en un objet structuré, appelé `DoclingDocument`. L'objet contient notamment des éléments textuels, tableaux, images et références à leur localisation. Il peut être sérialisé pour éviter de répéter une conversion coûteuse.

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("data/veltis/politique_teletravail_2025.docx")
print(result.status)
doc = result.document
print("Textes:", len(doc.texts), "Tableaux:", len(doc.tables))
texte_md = doc.export_to_markdown()
```

**Important :** le document du collègue et la démo mentionnent `SUCCESS`, `PARTIAL_SUCCESS` et `FAILURE`. Un statut ne garantit pas que les tableaux, titres et numéros de page aient été reconnus correctement : **vérifier un échantillon sur l'original**.

- **Body / furniture :** distinguer contenu du document et mobilier répétitif (en-têtes, pieds de page).
- **Provenance :** pour des éléments adaptés, `element.prov` fournit page et coordonnées. Cela permet de rattacher un passage à son emplacement, mais il faut vérifier que ces métadonnées se conservent après le chunking et l'indexation.
- **JSON vs Markdown :** conserver le JSON structuré comme résultat de conversion ; le Markdown est lisible et pratique, mais perd des informations de structure et de géométrie.

La démonstration du professeur est visible dans **`demo/02_intro_docling.ipynb`**. Il faut être capable d'expliquer la différence entre un `result`, son `result.document` et la version sauvegardée.

### 2.3 Contrôler la conversion plutôt que seulement la réussir

| Contrôle | Question à poser | Conséquence si échec |
|---|---|---|
| Nombre de pages | Correspond-il au PDF original ? | Une partie de la source peut manquer |
| Tableaux | Les colonnes/valeurs sont-elles associées ? | Valeurs citées hors contexte |
| Titres | Les sections sont-elles reconnaissables ? | Chunks difficiles à interpréter |
| OCR | Le scan produit-il du texte contrôlable ? | Passage absent de l'index |
| Provenance | La page est-elle retrouvable ? | Citation documentaire peu fiable |

## 3. L'ingestion est un ETL : la tracer dans PostgreSQL

Le professeur fait suivre chaque ingestion par un **journal de bord**. La table `run` contient une ligne par exécution ; la table `document` contient une ligne par document traité. Ton [schéma SQL disponible sur GitHub](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql) illustre `run_id`, `start_time`, `doc_processed`, `parameters JSONB`, `file_hash`, `status_`, compteurs et `error`.

```sql
-- EXEMPLE DE LECTURE SEULE pour le schéma run/document
SELECT r.run_id, r.start_time,
       COUNT(d.document_id) AS nb_documents,
       COUNT(*) FILTER (WHERE d.status_ = 'success') AS nb_succes
FROM run AS r
LEFT JOIN document AS d ON d.run_id = r.run_id
GROUP BY r.run_id, r.start_time
ORDER BY r.start_time DESC;
```

**Attention aux schémas différents.** Le notebook corrigé utilise également des tables nommées `runs` et `documents`, avec des colonnes différentes (`started_at`, `processed_count`, `sha256`, `status`, etc.). **Ne lance pas cette requête aveuglément** sur une base contenant l'autre schéma. Regarde d'abord `\dt` puis `\d run` ou `\d runs`.

### 3.1 Le SHA-256 et l'idempotence

L'empreinte SHA-256 identifie un **contenu**, pas son nom. Deux fichiers aux octets identiques ont la même empreinte ; un fichier modifié en change normalement. Le pipeline doit éviter de convertir plusieurs fois inutilement un document déjà réussi.

```python
from pathlib import Path
import hashlib

def empreinte(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

Pour **réutiliser** un résultat, vérifier les trois conditions :

1. Même empreinte et mêmes paramètres de conversion pertinents, ou règles explicites de versionnement.
2. Une conversion précédente terminée avec succès.
3. La sortie structurée attendue (`.json`) existe encore et est valide.

Sinon, retraiter ou signaler l'anomalie. Le paramètre `force=True` de l'exercice sert à forcer la conversion après une modification volontaire des réglages. L'erreur d'un fichier ne doit pas faire oublier les autres : elle doit être journalisée.

**Erreur relevée dans la synthèse du collègue :** une boucle de démonstration attribuait l'objet `doc` d'une cellule précédente à plusieurs résultats au lieu de `result.document`. Autre problème signalé : compteur d'erreurs vérifiant la clé `status` alors que les données utilisent `status_`. **Ce sont des points de vigilance remontés par la synthèse**, pas une affirmation sur l'état de toutes les versions du notebook.

## 4. Le chunking : découper sans détruire le sens

Un **chunk** est un fragment textuel à indexer. Trop petit : il perd sa phrase de contexte. Trop gros : il dilue les thèmes et peut dépasser la limite du modèle. Les titres, pages et tableaux doivent rester liés aux passages autant que possible.

| Méthode de découpe | Principe | Compromis |
|---|---|---|
| `LineBasedTokenChunker` | Regrouper selon les lignes et le budget de tokens | Peu respectueux de la structure |
| `HierarchicalChunker` | Respecter sections, paragraphes et objets du document | Chunks parfois très inégaux |
| `HybridChunker` | Partir de la structure puis ajuster à une limite de tokens | Bon point de départ à vérifier |

Le cours utilise le **tokenizer du modèle BGE-M3**. Le modèle d'embedding doit recevoir un texte qui reste dans son budget de tokens. Dans les notebooks, les objectifs testés comprennent 100 tokens, environ 400 tokens, ainsi qu'un jeu associé à **544 tokens**. Ces valeurs désignent un **réglage de découpe**, pas le nombre de documents.

```python
from transformers import AutoTokenizer
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker

modele = "models/embedder/bge-m3"  # chemin relatif à adapter
hf_tok = AutoTokenizer.from_pretrained(modele, local_files_only=True)
tok = HuggingFaceTokenizer(tokenizer=hf_tok, max_tokens=400)
chunker = HybridChunker(tokenizer=tok)

# 'doc' est un DoclingDocument déjà chargé
chunks = list(chunker.chunk(doc))
for morceau in chunks[:3]:
    print(chunker.contextualize(morceau))
```

**`contextualize()` est essentiel :** il ajoute les informations structurelles disponibles (par exemple les titres), qui aident à interpréter un paragraphe sorti de son document. Selon la version installée, les imports proposés peuvent évoluer ; le code ci-dessus correspond aux notebooks consultés.

**Exemple métier :** « Indemnité plafonnée à 50 € » est ambigu. « Télétravail > Conditions d'indemnisation > Indemnité plafonnée à 50 € » reste intelligible pour la recherche et la restitution. Il faut cependant citer le document et la page d'origine, et ne pas déduire une règle juridique depuis un fragment isolé.

### 4.1 Comparer 100 et 544 sans conclusions automatiques

Ton notebook `ex12-10-26_chunking_embeddings_100_vs_544_numpy.ipynb` construit une comparaison de recherche par cosinus **sans Qdrant**. Une configuration plus courte fournit généralement plus de passages et moins de contexte par passage ; une configuration longue fait l'inverse. **Il n'existe pas de taille gagnante universelle.** La choisir à partir de questions-test, puis mesurer la pertinence et la provenance des passages récupérés.

## 5. BGE-M3 : transformer un passage en vecteur

L'embedder n'écrit **pas** une réponse. Il calcule une représentation numérique utilisée pour comparer la question et les passages. Tes notebooks BGE-M3 montrent des vecteurs de **1 024 dimensions** dans la configuration consultée.

```python
from openai import OpenAI

# Requiert un serveur d'embeddings DÉJÀ démarré et accessible
client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="not-needed")
r = client.embeddings.create(model="bge-m3", input=["résilier un contrat", "mettre fin à l'abonnement"])
print("Nombre de vecteurs:", len(r.data))
print("Dimension du premier:", len(r.data[0].embedding))
```

**Réseau :** depuis le Z4, `127.0.0.1` peut convenir si le serveur écoute sur cette interface ; depuis un conteneur Docker, `localhost` pointe sur le conteneur lui-même. Dans B5, une adresse comme `172.21.0.1:8001` a été documentée pour joindre l'hôte. **Ce sont des configurations historiques à vérifier ; ne redémarre pas de modèle pour l'exercice.**

### 5.1 Similarité et distance cosinus

Deux fonctions souvent confondues :

- **Similarité cosinus :** plus grand = plus proche (maximum théorique 1).
- **Distance cosinus :** `1 - similarité` ; plus petit = plus proche (0 pour deux vecteurs identiques et non nuls).

`scipy.spatial.distance.cosine()` donne une **distance**. Un index Qdrant configuré en similarité cosinus présente un score à interpréter dans l'autre sens. Les textes « bien » et « mal » peuvent être proches vectoriellement parce qu'ils partagent des contextes linguistiques : un score ne prouve ni l'identité juridique ni l'absence de négation.

**Principe impératif :** les embeddings des documents et des questions doivent utiliser un espace vectoriel compatible, généralement obtenu avec le **même modèle/version/configuration**. En changer impose de recalculer les vecteurs du corpus.

## 6. Qdrant, recherche dense et recherche hybride

La synthèse du collègue s'arrêtait **avant l'étape Qdrant**, mais tes fichiers ultérieurs documentent la suite :

- [12/10 — Chunking 100 vs 544 et recherche NumPy](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex12-10-26_chunking_embeddings_100_vs_544_numpy.ipynb)
- [14/10 — Recherche Qdrant dense + sparse + fusion RRF](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex14-10-26_Qdrant_dense_sparse_hybrid_RRF.ipynb)
- [15/10 — Chaîne RAG avec LLM et PostgreSQL](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex15-10-26_RAG_100_LLM_PostgreSQL_REEXECUTABLE.ipynb)

| Recherche | Point fort | Risque à surveiller |
|---|---|---|
| Dense (embeddings) | Trouver des reformulations et synonymes | Oublier des noms ou références exactes |
| Sparse / BM25 | Trouver des termes, identifiants, noms précis | Rater des formulations équivalentes |
| Hybride / RRF | Fusionner des classements complémentaires | Plus de complexité ; gain à mesurer |

**RRF (Reciprocal Rank Fusion)** fusionne les **positions** des résultats de plusieurs méthodes, et non leurs scores bruts qui n'ont pas la même échelle. Il ne faut pas annoncer qu'une recherche hybride est meilleure sans tests comparatifs pertinents.

Pour alimenter Qdrant, un point doit conserver au minimum : `id` stable, texte du chunk, vecteur et **payload de provenance** (nom de fichier, page, titres, empreinte/document_id et version). Les informations de provenance présentes dans Docling ne deviennent pas automatiquement des citations ; il faut explicitement les transporter jusqu'au résultat de recherche.

## 7. Donner au LLM des sources et contrôler sa réponse

Une réponse RAG doit être fondée sur des passages réellement retrouvés. Exemple de contrat de réponse **pédagogique**, à adapter à ton application :

```text
Rôle : assistant documentaire.
Réponds uniquement à partir des extraits ci-dessous.
Chaque affirmation importante doit citer [document, page].
Si les extraits ne permettent pas de répondre, indique-le.
Ne transforme pas une hypothèse ou un ancien règlement en règle actuelle.

Question : ...
Extraits : [source X, page 3] ... ; [source Y, page 6] ...
```

Les contrôles ne peuvent pas reposer seulement sur l'instruction au modèle : il faut vérifier que les documents cités figurent dans les résultats de recherche, que les pages existent et que les passages soutiennent réellement la conclusion. Dans une application réglementaire future comme **TECHREG**, il faudra en plus stocker la version du texte et sa date de validité.

**Différence importante :** ton conseiller produit B5 est d'abord une **recherche sémantique dans un catalogue** avec règles de stock et historique conversationnel ; ce n'est pas, tel quel, un assistant de citations documentaires. L'architecture des embeddings se réutilise, mais il faut ajouter les sources et les contrôles documentaires pour parler d'un RAG juridique fiable.

## 8. Ce que ton dépôt prouve — et ce qu'il ne prouve pas

| Objet observé | Preuve disponible | Ce qu'il reste à démontrer sans aide |
|---|---|---|
| Extraction | Démo Docling et exercice ETL corrigé | Contrôler un scan et un tableau, journaliser un échec |
| Chunking | Notebook HybridChunker et comparaison 100/544 | Comparer deux configurations sur 5 questions |
| Embeddings | Notebook BGE-M3 et sorties enregistrées | Vérifier dimension, erreurs et cohérence des modèles |
| Recherche | Notebook Qdrant dense/sparse/RRF | Interpréter le score et retrouver la page source |
| Génération | Notebook RAG du 15/10 avec Nemotron | Justifier une réponse et refuser une question sans source |
| Industrialisation | B5 (API, PostgreSQL, n8n, tests) | Exécution de bout en bout et sauvegarde restaurable |

Le notebook du 15/10 contient des cellules exécutées enregistrées ; cela indique un travail opérationnel, mais **ne constitue pas une validation autonome du pipeline**. Les modèles locaux, leurs paramètres, les volumes et les bases doivent être contrôlés sur le Z4.

## 9. Journée d'étude : trois blocs autonomes de 45 minutes

### Bloc A — Audit de l'extraction (sans GPU, sans écriture)

**But :** identifier des sorties Docling sauvegardées et comprendre les fichiers disponibles. Depuis Ubuntu :

```bash
cd ~/formation/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/demo
find export_folder -maxdepth 1 -type f \( -name '*.json' -o -name '*.md' \) | sort | head -25
```

Choisis **un** document fictif Veltis dont tu disposes encore de l'original et du JSON. Ouvre le JSON **sans rien modifier**. Repère son nom, ses textes, ses tableaux et, si présents, les informations de page. Compare une section avec le document original.

**Livrable :** tableau de quatre lignes « objet source / texte extrait / problème / vérification possible ». Ne publie pas de document restreint.

### Bloc B — Test de chunking : expliquer avant de calculer

Sur papier d'abord, prends un texte fictif de 3 sections (200–400 mots). Décris ce qu'un chunker ligne, hiérarchique puis hybride produirait. Ensuite, examine les cellules correspondantes de ton notebook `demo_chunking_embedding.ipynb` et de celui du 12/10.

Sans lancer les embeddings, complète une matrice :

| Mesure | 100 tokens | 400/544 tokens |
|---|---|---|
| Nombre de chunks | À relever | À relever |
| Titres conservés ? | À contrôler | À contrôler |
| Une réponse est-elle coupée entre deux chunks ? | À contrôler | À contrôler |
| Page et nom de fichier conservés ? | À contrôler | À contrôler |

**Livrable :** une recommandation de taille **conditionnelle** à trois questions-test, pas une conclusion générale.

### Bloc C — Dessiner une recherche vérifiable

À partir d'une question fictive sur la **politique de télétravail Veltis**, indique : question → embedding → trois passages récupérés → source/page → réponse. Ajoute un **contre-exemple** : une question absente du corpus, à laquelle l'assistant doit refuser de répondre.

Si les services tournent déjà, un **test non destructif** possible depuis l'hôte est `curl --max-time 4 http://127.0.0.1:8001/v1/models`. Une réponse d'erreur n'autorise pas à relancer spontanément vLLM. N'effectue aucune création/suppression de collection pour ce cours.

**Livrable :** un schéma annoté et cinq critères de contrôle (justesse, preuve, page, version, refus).

## 10. Autotest — réponse sans ouvrir les notebooks

1. Quelle est la différence entre extraction, chunking et embeddings ?
2. Pourquoi stocker un `DoclingDocument` en JSON en plus du Markdown ?
3. Que signifie la provenance d'un élément extrait ?
4. Quelles trois conditions vérifier avant d'éviter un retraitement Docling ?
5. Pourquoi le nom d'un PDF ne suffit-il pas pour détecter une modification ?
6. Que fait `contextualize(chunk)` ?
7. Un cosinus de distance de `0,10` est-il meilleur ou moins bon que `0,70` ?
8. Pourquoi un score dense et un score BM25 ne doivent-ils pas être additionnés directement ?
9. Quelle preuve manque lorsqu'un LLM donne une page inventée ?
10. Quelle différence technique sépare un pipeline RAG documentaire du projet B5 actuel ?

### Corrigé bref

1. Extraction = récupérer/structurer ; chunking = découper ; embedding = encoder numériquement.
2. Le JSON conserve davantage de structure et métadonnées, utile pour réexécuter sans OCR.
3. Le rattachement de l'élément à une source, notamment à une page ou zone localisable.
4. Même contenu/paramètres pertinents, succès préalable, sortie JSON existante et valide.
5. Un fichier peut changer sans être renommé ; utiliser une empreinte du contenu.
6. Ajoute le contexte structurel (par exemple les titres) à la représentation du passage.
7. **Meilleur** : en distance cosinus, la valeur basse est la plus proche.
8. Échelles différentes ; RRF fusionne les rangs, ou utiliser une normalisation explicitement évaluée.
9. Il manque un lien vérifié entre l'affirmation et le passage/page source.
10. B5 cherche des produits et applique des règles de stock ; le RAG documentaire doit aussi conserver des passages citables et vérifier leur soutien aux réponses.

**Seuil d'autonomie pour ce cours :** expliquer au moins 8 réponses correctement, puis produire les livrables A, B et C sans laisser l'IA écrire les étapes techniques de base. Si cela échoue, revenir au module manquant plutôt que de simplement relire tout le cours.

## 11. Références exactes pour poursuivre la lecture

**Support du collègue (source utilisateur)**
- `2026 Cours.zip` → `2026-10-02_09 - RAG, extraction et chunking (Docling).md`. Synthèse reconstruite ; pas de notes manuscrites fournies.

**Notes/démos du professeur conservées dans ton GitHub**
- [Installation et services RAG — `demo/00_setup.md`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/demo/00_setup.md)
- [Extraction et structure — `demo/02_intro_docling.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/demo/02_intro_docling.ipynb)
- [Suivi ETL — schéma `run` / `document`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo/queries/schema.sql)

**Tes prolongements observables**
- [Exercice ETL tracé dans PostgreSQL — corrigé](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/corrige/exercice_01_pipeline_corrige.ipynb)
- [Chunking et embeddings — `demo_chunking_embedding.ipynb`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb)
- [Comparaison 100/544 avec NumPy — 12/10](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex12-10-26_chunking_embeddings_100_vs_544_numpy.ipynb)
- [Qdrant et fusion RRF — 14/10](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex14-10-26_Qdrant_dense_sparse_hybrid_RRF.ipynb)
- [RAG, Nemotron et PostgreSQL — 15/10](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/drive-download-20261008T064617Z-1-001/rag/ex15-10-26_RAG_100_LLM_PostgreSQL_REEXECUTABLE.ipynb)
- [B5, application Python et recherche sémantique](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py)

**Documentation indépendante utilisée pour vérification**
- [Docling — chunking et contextualisation](https://docling-project.github.io/docling/concepts/chunking/)
- [Qdrant — recherche hybride et RRF](https://qdrant.tech/documentation/search/hybrid-queries/)

**Suite prévue :** cours 15, « ETL avec Zparse ». Il complétera ce chapitre ; nous ne lancerons pas un nouveau projet tant que les exercices de consolidation ne sont pas validés.
