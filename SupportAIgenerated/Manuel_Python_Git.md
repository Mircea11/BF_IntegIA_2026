# Manuel personnel — Environnements Python, dépendances et gestion de plusieurs projets Git

**HP Z4 / Ubuntu · Formation AI Integration Specialist · 27 octobre 2026**  
**Document autonome**, complémentaire au cours 10 (Git) et aux cours 2, 7, 11 à 15.  
**But :** pouvoir ouvrir un projet, identifier son Python et ses bibliothèques, reproduire son environnement, modifier son code et enregistrer *uniquement* les bons fichiers dans Git, sans interrompre les autres projets.

> **Périmètre et limites.** Les exemples « dépôt vérifié » proviennent de `Mircea11/BF_IntegIA_2026` consulté le 27/10/2026. Les commandes de diagnostic sont à exécuter sur ton Z4 ; leur résultat réel n'a pas été observé ici. Aucun environnement n'a été installé ou modifié sur ton ordinateur pour préparer ce manuel. Des dossiers absents du GitHub public peuvent exister localement. N'exécute pas les commandes de création ou d'installation dans `~/formation` par simple copier-coller.

## 0. Page de référence : les six décisions à prendre avant chaque intervention

1. **Quel projet ?** `pwd`, puis `git rev-parse --show-toplevel`. Un sous-dossier de `~/formation` peut être un projet Python distinct, mais il dépend du **même historique Git** si aucun `.git` séparé n'est présent.
2. **Quel Python ?** `python --version`, `command -v python`, `python -c 'import sys; print(sys.executable)'` ; pour un notebook, vérifier `sys.executable` *dans la cellule*.
3. **Quel gestionnaire ?** `pyproject.toml` + `uv.lock` → généralement `uv` ; `requirements.txt` → souvent `venv` + `pip` ; `docker-compose.yaml` → ajoute un environnement de conteneurs, qui n'est pas une `.venv`.
4. **Quels services externes ?** PostgreSQL, Qdrant, n8n, vLLM et leurs ports sont des processus/services distincts ; installer un paquet Python ne les démarre pas.
5. **Qu'est-ce qui change ?** Code, manifeste, fichier de verrouillage, données de démonstration ? Les secrets, modèles, bases et fichiers temporaires ne doivent pas devenir des commits par accident.
6. **Quel périmètre de commit ?** `git status -sb` → `git add -- chemin/...` → `git diff --cached --name-status` → test → commit. Faire un `push` uniquement après vérification des fichiers et du distant.

**Règle pratique : un projet = un but = un jeu de dépendances maîtrisé = un README d'installation.** Un même dépôt Git peut contenir plusieurs projets, mais il ne doit pas les confondre.

## 1. Modèle mental : sept couches différentes

```text
Ordinateur Z4 (Linux)
  Python système / Python géré par uv / pilotes GPU
     ├── Projet A indépendant : pyproject.toml + uv.lock ──> .venv A
     ├── Projet B indépendant : requirements.txt ───> .venv B
     └── Projet C : serveur vLLM ────────────────────> environnement dédié C

Code Python ──importe──> bibliothèques présentes dans SON environnement
Code Python ──lit───────> paramètres .env (si l'application les charge)
Code Python ──appelle────> services HTTP / PostgreSQL / Qdrant / n8n
Git ──versionne─────────> code + manifests + tests + documentation (pas .venv/.env)
GitHub ──héberge─────────> commits envoyés par git push
```

- **Interpréteur Python** : exécutable qui lance le programme (`python`, `python3`, chemin absolu). Un Z4 peut héberger plusieurs versions.
- **Environnement virtuel (`.venv/`)** : dossier de binaires et de bibliothèques installé pour *un projet*. Il isole des dépendances ; il n'isole pas les services Docker ni les variables d'environnement du système entier.
- **Paquet / module** : code importable, par exemple `requests`, `docling`, `numpy`, `psycopg`. Le nom d'installation et le nom d'import ne sont pas toujours identiques (`python-dotenv` → `dotenv`).
- **Dépendance directe** : bibliothèque choisie pour le projet. **Dépendance transitive** : bibliothèque exigée par une autre bibliothèque.
- **Variable d'environnement** : réglage de processus (`QDRANT_URL`, `HF_TOKEN`, `CUDA_VISIBLE_DEVICES`). Un `.env` est un *fichier texte facultatif* qui peut fournir ces variables ; Python ne le charge pas automatiquement.
- **Service** : programme indépendant exposant un port (n8n, PostgreSQL, Qdrant, vLLM). Les *identifiants* et chemins dépendent de l'endroit où tourne le client : Z4 ou conteneur.
- **Git** : suit des fichiers et leur historique ; il ne sauvegarde pas les paquets de `.venv` ni l'état courant des conteneurs.

## 2. Reconnaître les fichiers : garder, ignorer, comprendre

| Élément | Rôle réel | Versionner dans Git ? | Piège courant |
|---|---|---|---|
| `pyproject.toml` | Nom du projet, Python compatible, dépendances directes, configuration outils, `uv` workspace | **Oui** | Le fichier seul ne garantit pas qu'un environnement fonctionne |
| `uv.lock` | Résolution exacte des dépendances d'un projet/workspace `uv` | **Oui**, normalement | Ne pas le modifier à la main ; peut concerner tout un workspace |
| `.python-version` | Version demandée à `uv`/outils compatibles (ex. `3.12`) | **Oui** | Ne crée pas l'interpréteur à lui seul |
| `.venv/` | Python virtuel, paquets, exécutables | **Non** | Non portable ; une `.venv` peut masquer un autre Python |
| `requirements.txt` | Liste des paquets à installer avec `pip` / `uv pip` | **Oui** | Souvent sans verrouillage complet des transitives |
| `.env` | Valeurs locales : adresses, secrets, options | **NON** | N'est ni un environnement virtuel ni une liste de dépendances |
| `.env.example` | Gabarit **sans vrais secrets** | **Oui**, si explicitement non ignoré | Copier sans publier le fichier rempli |
| `.gitignore` | Règles qui évitent de *commencer* à suivre certains fichiers | **Oui** | N'efface pas les fichiers déjà suivis par Git |
| `README.md` | Comment installer, exécuter, tester, restituer | **Oui** | Doit différencier prérequis et résultats prouvés |
| `src/`, `app.py`, `tests/` | Code source, application et tests | **Oui** | Ne pas y mettre de secrets ni de chemins privés obligatoires |
| `__pycache__/`, `.pytest_cache/` | Caches régénérables | **Non** | Leur présence dans `git status` ne prouve aucun progrès |
| `*.ipynb` | Code + métadonnées + parfois sorties sauvegardées | **Oui, après revue** | Les cellules peuvent exposer données, sorties et chemins privés |
| `models/`, `*.gguf`, `*.safetensors` | Poids volumineux de modèles | **En général non** | Le Git du cours n'est pas une sauvegarde de modèles |
| `Dockerfile`, `compose.yaml` | Définition d'images et services | **Oui si nettoyés** | Secrets en dur / ports accessibles au public |
| Volumes Docker / BDD | Données réelles persistantes des services | **Non, sauvegarde séparée** | `git push` ne sauvegarde pas les données PostgreSQL/Qdrant |
| `.git/` | Historique, index et métadonnées locales Git | **Ne pas copier manuellement** | Un `git init` au mauvais niveau crée un dépôt imbriqué |

**Deux mots presque identiques, deux choses incompatibles :** `.env` = configuration ; `.venv` = dossier de bibliothèques. `.vencv` n'est pas le nom standard.

## 3. Ton dépôt réel : inventaire vérifié et problèmes identifiés

Dépôt : `Mircea11/BF_IntegIA_2026`. GitHub montre désormais les commits `d69d3a5`, `5d2f29e`, `ba38a3786` et `c26fd6cb3` ; **la publication a donc abouti** au moment de cette consultation. Cela ne dit rien de l'état de ton répertoire local au moment de la lecture.

| Emplacement publié | Fichiers observés | Signification opérationnelle |
|---|---|---|
| Racine du dépôt | `pyproject.toml`, `uv.lock`, `.python-version = 3.12`, `Created_enviroment_uv_version.txt` | Environnement de formation **global** initié sur Windows ; ne pas supposer qu'il est adapté à chaque sous-projet Linux |
| `RAG/cours-rag/` | `pyproject.toml` : Docling, `qdrant-client`, `psycopg`, `transformers`, `python-dotenv`… | Sous-projet RAG avec ses propres dépendances déclarées |
| `formation/vLLM/cours_llama/` | `pyproject.toml`, `.python-version = 3.12`, notebooks | Client/API pédagogique ; les dépendances déclarées n'installent **pas** nécessairement le serveur vLLM |
| `formation/vLLM/vllm_server/` | `pyproject.toml` avec `dependencies = []` | Manifeste trop minimal pour prouver une reproduction de l'environnement vLLM réel |
| `deeplearning/deeplearning1/` | `pyproject.toml` : Keras, TensorFlow, Torch, etc. | Environnement lourd et différent de celui du RAG |
| `deeplearning/` | `pyproject.toml`, `uv.lock`, section `[tool.uv.workspace]` | Workspace local ; plusieurs membres peuvent partager un lockfile |
| `N8N/B5_conseiller_produit_v2/` | `requirements.txt`, `setup.sh`, `run.sh`, `.gitignore` | Application FastAPI avec `.venv` créée par le script, sans manifeste `uv` dédié |
| `N8N/` | `env.example`, exercices JSON, workflow n8n, configuration Compose sauvegardée | **n8n est dans Docker**, pas dans un environnement virtuel Python n8n |

**Particularité déterminante :** deux fichiers `pyproject.toml` ne garantissent pas deux `.venv` distinctes. Les membres d’un même **workspace uv** partagent normalement l’environnement et le lockfile de la racine du workspace. Les projets indépendants utilisent leurs environnements séparés.

**Vérification importante, sans modifier ton dépôt :** le `pyproject.toml` racine déclare un workspace contenant notamment `Specialist_IA/Polars`, `dataframes_polars` et `formation/vLLM/full_llama_vllm/cours-rag`. Ces trois chemins **ne sont pas présents dans l'arbre GitHub public consulté**. Ils peuvent être locaux, exclus ou supprimés. En conséquence, **ne lance pas `uv sync` à la racine** avant d'avoir contrôlé ces membres : cela peut échouer à résoudre le workspace et/ou modifier des paquets installés. Un workspace partage un seul lockfile, donc une erreur d'un membre peut affecter tous les autres.

**Autres particularités observées :** la racine déclare `dotenv` *et* `python-dotenv`, ainsi que `psycopg2-binary` *et* `psycopg[binary]`. Ce n'est pas automatiquement faux, mais il faut vérifier lesquels sont réellement importés. `formation/docker-httpd/pyproject.toml` porte le nom `cours-llama` : probable réemploi d'un gabarit, à vérifier avant de le présenter comme un projet indépendant propre.

**Note de provenance :** `Created_enviroment_uv_version.txt` consigne une séance PowerShell Windows : `uv venv --python 3.12` exécuté une fois dans le dossier utilisateur et une autre fois dans `Desktop/BF_IntegIA_2026`, puis `uv init` et `uv add numpy`. Cela a créé **deux environnements distincts**, pas un environnement transférable sur le Z4. Le fichier est un journal d'apprentissage, pas un script de restauration.

## 4. Diagnostiquer sans rien changer : la procédure Z4 de référence

À exécuter **avant** d'ajouter, installer, réinitialiser ou synchroniser des dépendances :

```bash
cd ~/formation
pwd
printf '\nDEPOT GIT :\n'
git rev-parse --show-toplevel
git status -sb
printf '\nPYTHON / UV :\n'
command -v python || true
command -v python3
python3 --version
command -v uv || true
uv --version  # uniquement si uv est disponible
printf '\nENVIRONNEMENT COURANT :\n'
python3 -c 'import sys; print(sys.executable); print("prefix:", sys.prefix); print("base:", sys.base_prefix)'
printf '\nFICHIERS RACINE :\n'
ls -la pyproject.toml uv.lock .python-version .gitignore 2>/dev/null
```

Interprétation :
- `sys.prefix != sys.base_prefix` suggère un environnement virtuel en cours.
- `python3` peut **ne pas** être le même interpréteur que `python` ; teste le programme effectivement utilisé.
- La présence de `.venv` dans un projet ne prouve pas qu'il soit actif. `uv run` peut lancer celui du projet sans activation manuelle.
- Le prompt `(vllm_server)` n'est pas une preuve suffisante ; vérifier `sys.executable`.
- À la racine de `~/formation`, `git status` inclut des changements de **N8N, RAG, formation et deeplearning** : Git ignore les frontières pédagogiques des dossiers.

Pour une vue limitée aux *noms de fichiers* de gestion :

```bash
cd ~/formation
find . -maxdepth 4 \( -name pyproject.toml -o -name requirements.txt \
  -o -name uv.lock -o -name .python-version -o -name .env.example \) -print
```

Ne pas utiliser `cat .env`, `printenv`, `env` ou `set` dans une capture publique : ces commandes peuvent dévoiler des secrets.

## 5. Créer un NOUVEAU projet indépendant avec `uv` (laboratoire sûr)

**Faire cet exercice dans un dossier neuf *hors* de `~/formation`** pour éviter que `uv init` ne l'ajoute au workspace de la racine. Sur le Z4 :

```bash
mkdir -p ~/lab-python/etl-demo
cd ~/lab-python/etl-demo
uv init --app --python 3.12
ls -la                         # examiner les fichiers créés
uv add requests python-dotenv
uv add --dev pytest ipykernel
uv run python -c 'import sys, requests; print(sys.executable); print(requests.__version__)'
uv tree                         # liste des dépendances résolues
```

`uv init` définit le projet ; `uv add` écrit les dépendances dans `pyproject.toml`, résout un `uv.lock` et prépare l'environnement du projet ; `uv run` lance une commande dans cet environnement. Selon la version et le modèle utilisé, `uv init --app` peut créer `main.py` ou une autre structure : **regarder réellement `ls -la`**. Les ajouts et la résolution peuvent télécharger des paquets ; ces commandes sont **volontairement mutantes**, à réaliser exclusivement dans le laboratoire.

Créer un programme minimal en choisissant d'abord le bon fichier :

```python
# main.py (exemple du laboratoire si ce fichier existe ou est créé)
import os
import requests
from dotenv import load_dotenv

load_dotenv()
print('Interpréteur actif : OK')
print('URL API configurée :', os.getenv('API_BASE_URL', 'https://example.org'))
print('Bibliothèque requests :', requests.__version__)
```

Exécution : `uv run python main.py`. Tu n'as pas besoin de `source .venv/bin/activate` pour `uv run`.

**Quand le projet existe déjà :** après avoir lu son `README` et confirmé son périmètre, `uv sync --locked` installe les paquets correspondant au verrouillage *sans recalculer celui-ci* ; **mais il modifie `.venv` et peut supprimer des paquets supplémentaires**. Ne le lance pas dans le dépôt global de formation. Pour expliquer la différence : `uv lock` calcule/actualise le verrouillage, `uv sync` installe, `uv run` exécute et peut synchroniser, `uv add` modifie la liste des dépendances. `--locked` demande que le lockfile soit déjà cohérent ; `--frozen` utilise le fichier existant sans vérifier son actualité, ce n'est pas une garantie de cohérence.

## 6. Créer un environnement classique avec `venv` et `pip`

Solution lorsque le projet contient **`requirements.txt` mais pas de `pyproject.toml`**, comme B5 :

```bash
mkdir -p ~/lab-python/pip-demo
cd ~/lab-python/pip-demo
python3 -m venv .venv
source .venv/bin/activate
python -m pip --version
python -m pip install requests
python -c 'import sys, requests; print(sys.executable); print(requests.__version__)'
deactivate
```

Expliquer chaque ligne :
- `python3 -m venv .venv` crée un dossier isolé avec la version correspondant à `python3`.
- `source .venv/bin/activate` modifie `PATH` **pour ce terminal**, jusqu'à `deactivate` ou la fermeture du shell.
- `python -m pip` garantit que `pip` appartient au Python invoqué. Préférer cela à un `pip` dont le chemin est inconnu.
- Pour exécuter sans activation : `./.venv/bin/python main.py` ou `./.venv/bin/python -m pip list`.
- Pour un projet existant : `python -m pip install -r requirements.txt` **dans le bon environnement**. N'installe pas les bibliothèques de formation directement dans le Python système (`sudo pip install` est à éviter).

**Windows PowerShell, d'après tes notes de juillet :** l'activation s'écrit `.venv\Scripts\Activate.ps1` ; sur Ubuntu, `source .venv/bin/activate`. La commande `Set-ExecutionPolicy` ne s'applique pas à Linux. Déplacer `.venv` de Windows vers Linux n'est pas une méthode de transfert.

## 7. `pyproject.toml`, `uv.lock`, `requirements.txt` : qui commande quoi ?

**Projet uv classique :**

```toml
[project]
name = "etl-demo"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = ["requests>=2.31,<3", "python-dotenv>=1,<2"]

[dependency-groups]
dev = ["pytest>=8,<10", "ipykernel>=6"]
```

Ce sont des valeurs **pédagogiques**, pas la copie de ton `pyproject.toml` de production. `requires-python = ">=3.12"` autorise aussi des versions supérieures ; ce n'est pas équivalent à **Python exactement 3.12**. `.python-version` donne à `uv` une version *préférée* ; `uv.lock` fixe les versions **résolues** des dépendances, sous les contraintes indiquées. Une installation reste dépendante de la plateforme et de la disponibilité de roues compatibles (notamment CUDA/Torch).

| Besoin | Projet `uv` propre | Projet `pip` classique |
|---|---|---|
| Créer l'isolement | `uv init ...` puis `uv add`/`uv sync` | `python3 -m venv .venv` |
| Installer une bibliothèque | `uv add requests` | `python -m pip install requests` |
| Bibliothèque de test | `uv add --dev pytest` | `python -m pip install pytest` |
| Exécuter | `uv run python main.py` | `.venv/bin/python main.py` |
| Reconstruire | `uv sync --locked` (projet valide) | `python -m pip install -r requirements.txt` |
| Vérifier la dépendance | `uv tree`, `uv pip list` (dans bon environnement) | `python -m pip list` |
| Sauvegarder les exigences | `pyproject.toml` + `uv.lock` | `requirements.txt` + contraintes/README |

**Ne pas mélanger par réflexe :** dans un projet `uv` géré, `uv pip install` ou `pip install` peut ajouter une bibliothèque qui n'est inscrite ni dans `pyproject.toml` ni dans `uv.lock`. Une future synchronisation peut la retirer. Utilise `uv add` pour une dépendance durable. `pip freeze` peut servir à *inspecter* un environnement mais sa liste contient les transitives : ce n'est pas le manifeste métier le plus clair.

## 8. Lancer le bon noyau Jupyter / VS Code

Dans un notebook, ajoute temporairement une cellule :

```python
import sys
import importlib.util
print('Python du notebook :', sys.executable)
print('Version :', sys.version)
print('numpy trouvable :', bool(importlib.util.find_spec('numpy')))
```

**Dans VS Code :** `Python: Select Interpreter` ou `Select Kernel` → choisir la `.venv` du **projet concerné**. Tu peux avoir simultanément un notebook RAG et un notebook de deep learning ; chacun doit utiliser son propre interpréteur. Dans un projet `uv`, `uv add --dev ipykernel` puis `uv sync` rendent le noyau disponible ; dans un projet `pip`, installer `ipykernel` dans la bonne `.venv`.

**Symptôme classique :** `ModuleNotFoundError` alors que tu as « installé » le paquet. Causes probables : terminal A et notebook B utilisent des interpréteurs différents, installation globale accidentelle, mauvais nom de paquet/import ou environnement sélectionné incorrect. Comparer leurs `sys.executable` **avant** de réinstaller quoi que ce soit.

## 9. `.env` et secrets : séparer paramètres, code et données

Exemple de **gabarit publiable** `.env.example` :

```dotenv
# Valeurs non sensibles uniquement : à adapter localement.
QDRANT_URL=http://127.0.0.1:6333
LLM_URL=http://127.0.0.1:8000/v1
POSTGRES_USER=example_user
POSTGRES_PASSWORD=REPLACE_ME_WITH_LOCAL_SECRET
```

Procédure **uniquement dans le laboratoire** :

```bash
cp .env.example .env
chmod 600 .env
# Modifier .env localement, ne jamais le publier.
```

Lire dans Python :

```python
import os
from dotenv import load_dotenv
load_dotenv()  # cherche .env ; dans une application complexe, définir un chemin explicite
qdrant_url = os.getenv('QDRANT_URL')
if not qdrant_url:
    raise RuntimeError('QDRANT_URL manquant')
```

`os.getenv()` sans `load_dotenv()` fonctionne uniquement si la variable existe déjà dans l'environnement du processus. Les clés doivent rester hors des logs, notebooks, captures d'écran et exports n8n. Ne pas publier une vraie clé même dans `.env.example`.

**Dans ton dépôt :** `N8N/env.example` existe et contient des valeurs fictives pour PostgreSQL et une variable d'encryption n8n à remplir. Le `.gitignore` racine utilise `**/.env.*` et une exception `!**/.env.example` ; la seconde ligne rend à nouveau publiables les *gabarits*, pas les vrais secrets. Vérifier concrètement :

```bash
cd ~/formation
git check-ignore -v N8N/.env  # affiche la règle, si le fichier est ignoré
git check-ignore -v N8N/env.example || true  # attention : nom 'env.example' SANS point initial
```

**Nuance importante :** `N8N/env.example` **n'est pas** `.env.example`. Il est suivi sur GitHub et reste un gabarit correct tant que ses valeurs sont fictives ; son nom ne bénéficie pas automatiquement de l'exception `!**/.env.example`. Les vrais secrets ne doivent pas être ajoutés au Git, même si une règle échoue. Si un secret a déjà été committé : révoquer/remplacer le secret, vérifier son historique et envisager une purge ; `git rm` seul ne suffit pas.

## 10. Docker, n8n, RAG et vLLM : quatre frontières d'exécution

Ton Z4 utilise plusieurs couches. Ne les fusionne pas dans ta tête :

| Élément | Où il fonctionne | Comment les dépendances sont gérées |
|---|---|---|
| B5 FastAPI | Processus Python hôte (`app.py`, `run.sh`) | `N8N/B5_conseiller_produit_v2/requirements.txt` + `.venv` créée par `setup.sh` |
| n8n | Conteneur Docker | Image Docker n8n ; nœuds JS internes et variables configurées dans l'instance |
| PostgreSQL / Qdrant | Conteneurs Docker dans les exercices B5 | Images, volumes, connexions réseau et identifiants |
| Nemotron / BGE-M3 | Serveurs vLLM sur le Z4, dans un autre environnement Python | Installation vLLM propre, modèles locaux et GPU ; les clients utilisent HTTP |
| Notebook RAG | Jupyter et son noyau Python | `pyproject.toml`/dépendances du projet + accès réseau aux services |

**L'adresse `localhost` change selon l'endroit :** dans un conteneur Docker, `127.0.0.1` désigne le conteneur lui-même, pas nécessairement ton PC. Dans un même réseau Compose, n8n peut joindre PostgreSQL par le nom du service (`postgres:5432`). Depuis le Z4, il faut le port publié sur l'hôte, par exemple `127.0.0.1:5433` *si c'est celui que Docker expose*. L'adresse `172.21.0.1` utilisée dans tes scripts B5 est **une hypothèse de ton ancien réseau Z4**, pas une adresse universelle ou garantie aujourd'hui.

**Deux usages différents du mot « env » dans Docker Compose :**
- Le fichier `.env` proche du Compose peut fournir des variables pour **interpoler** des expressions `${VAR}` dans la configuration Compose.
- `env_file:` ou `environment:` introduit des variables **dans le conteneur** ; ces mécanismes ne sont pas interchangeables automatiquement.

Les volumes Docker conservent des données **hors Git**. Avant une manipulation sur les services, inspecter `docker compose ps`, `docker ps`, `docker volume ls`. Ne jamais utiliser `docker compose down -v`, `docker volume prune` ou des suppressions de conteneurs pour « nettoyer » sans sauvegarde testée.

## 11. Serveurs LLM et GPU : pourquoi leurs environnements doivent rester distincts

Ton projet `formation/vLLM/cours_llama/pyproject.toml` déclare `openai`, `requests` et `polars` : il décrit avant tout une **application cliente pédagogique**. Le `pyproject.toml` de `formation/vLLM/vllm_server/` ne déclare aucune dépendance ; ce fichier ne suffit pas à réinstaller le serveur vLLM réellement utilisé. Le dépôt contient des notebooks lourds Keras/TensorFlow/Torch dans un autre sous-projet.

Règle : **ne pas installer TensorFlow, Torch et vLLM au hasard dans la même `.venv`**. Ils ont des contraintes spécifiques de versions Python, CUDA et roues GPU ; une simple installation peut changer les versions compatibles et casser le serveur fonctionnel.

Pour identifier le serveur **sans modification** :

```bash
command -v vllm || true
ps -eo pid,cmd | grep '[v]llm' || true
nvidia-smi  # seulement si installé ; lecture de l'état GPU
```

Les lignes de commande conservées dans `README_SETUP_FR.md` documentent des paramètres historiques ; avant un lancement, vérifier ports, processus existants, chemin local des modèles et VRAM. **Ne jamais démarrer une seconde instance pour « tester » si la première occupe déjà le GPU.**

## 12. Git : gérer plusieurs projets et mises à jour sans les mélanger

### 12.1. Trois niveaux à distinguer

- **Dépôt Git** : `~/formation` — il contient `N8N/`, `RAG/`, `deeplearning/`, `ETL/`, etc. **Une seule branche `main` partage l'historique de tous ces dossiers**.
- **Projet Python** : sous-dossier avec `pyproject.toml` et/ou `requirements.txt` ; il a son propre environnement. Ce n'est pas automatiquement un dépôt Git indépendant.
- **Expérience / tâche** : exercice A.2 n8n, notebook 06 RAG, correction du B5 — chaque changement devrait être testable et committé avec un périmètre précis.

Un `git status` lancé depuis `~/formation/RAG/cours-rag` reste celui du **même dépôt** et montre des changements ailleurs. Un `git add .` effectué depuis la racine peut sélectionner les autres projets ; le problème n'est pas réglé par `.gitignore` si ces fichiers sont légitimes mais ne doivent pas être publiés *dans ce commit*.

### 12.2. Séquence sûre — un commit « exercice N8N »

```bash
cd ~/formation
pwd
git rev-parse --show-toplevel
git status -sb

# EXEMPLE SEULEMENT, si tu as revu CE fichier et confirmé qu'il est publiable :
git add -- 'N8N/Exercice A.2.json'

git diff --cached --name-status
git diff --cached --check
git diff --cached -- 'N8N/Exercice A.2.json'  # inspecte le contenu sélectionné

# Puis, seulement si le contenu indexé correspond à ta tâche :
git commit -m 'Document n8n A2 weather workflow'
# Ensuite, examiner la connexion et le distant avant git push origin main.
```

**Attention :** `git commit` prend *tout ce qui est déjà indexé*, pas seulement le fichier que tu viens d'ajouter. Toujours vérifier `git diff --cached --name-status`. Si tu vois du RAG au lieu de n8n : `git restore --staged -- chemin/incorrect` enlève le fichier de l'index **sans supprimer sa copie locale**.

### 12.3. Travailler en branches séparées

Pour une fonctionnalité nouvelle, préférer une branche dédiée **quand l'arbre de travail est propre et la synchronisation comprise** :

```bash
git status -sb
git switch -c feature/n8n-validation-a2
# modifier, tester, indexer les seuls fichiers de cette tâche
# git commit ...
# git push -u origin feature/n8n-validation-a2  # APRES contrôle de connexion/secret
```

Le nom de branche reflète l'objectif, pas le langage. Une branche `feature/rag-reranker` peut préserver un essai technique tant qu'il n'est pas prêt pour `main`. Si le dépôt contient déjà des modifications non committées dans d'autres projets, **ne change pas de branche aveuglément**. Examiner d'abord les fichiers et décider s'il faut terminer, créer un checkpoint ou ranger les changements. Une pull request est utile pour revue avant fusion sur `main` ; les opérations directes sur `main` restent possibles mais comportent plus de risques.

### 12.4. Statuts à savoir lire

| Git affiche | Cela veut dire | Décision |
|---|---|---|
| `?? fichier` | Nouveau fichier local non suivi | Le publier ? le documenter ? l'ignorer ? |
| ` M fichier` | Fichier déjà suivi, modifié non indexé | Lire `git diff -- fichier` |
| ` D fichier` | Fichier suivi supprimé localement | Restaurer **ou** committer la suppression : c'est un choix métier |
| `A  fichier` | Nouveau fichier ajouté à l'index | Inspecter la version indexée |
| `D  fichier` | Suppression déjà prête pour le commit | Vérifier que c'est intentionnel |
| `[ahead 2]` | Deux commits locaux non intégrés dans la référence locale distante connue | `git push` encore à confirmer côté serveur |
| `[behind 1]` | Copie locale distante en avance d'un commit | `git fetch`, puis évaluer l'intégration |

**Dans ton cas du 26 octobre :** des fichiers supprimés volontairement étaient d'abord vus comme `D`, puis ont été enregistrés avec `git rm` dans `d69d3a5`. Les nouveaux exercices ont été sélectionnés explicitement et enregistrés dans `5d2f29e`. C'est le comportement voulu : supprimer des anciens fichiers *du dépôt* exige un commit, alors qu'ignorer leurs versions futures exige `.gitignore`. Les commits sont maintenant visibles sur GitHub.

### 12.5. Ce que `git add`, `commit`, `push`, `fetch`, `pull` et `rebase` ne font PAS

| Opération | Effet | Ce qu'elle ne garantit pas |
|---|---|---|
| `git add` | Prépare des versions de fichiers dans l'index | Ne sauvegarde rien à distance |
| `git commit` | Enregistre un instantané local | N'envoie rien à GitHub |
| `git push` | Transfère des commits si accès et historique compatibles | Ne sauvegarde pas les fichiers non suivis / la base Docker |
| `git fetch` | Met à jour les références du distant | Ne fusionne pas automatiquement ton travail |
| `git pull` | Fetch + intégration de l'historique | Peut provoquer conflits ou rebase selon configuration |
| `git rebase` | Rejoue des commits sur une autre base | Change les SHA des commits rejoués |
| `.gitignore` | Évite le suivi de certains fichiers futurs | Ne retire pas les fichiers déjà indexés ou publiés |

**Pratiques interdites comme dépannage automatique :** `git add .` sans examen ; `git reset --hard` ; `git clean -fd` ; `git push --force` ; `docker compose down -v`. Certains de ces outils ont des usages légitimes, mais pas comme réflexe sur ton dépôt de formation.

## 13. SSH / GitHub : correction de l'ancien cours 10

Le cours 10 contient un passage présentant une clé SSH particulière et le port 443 comme **configuration historiquement fonctionnelle**. **Cette affirmation n'avait pas une preuve terminale suffisante dans les échanges disponibles ; ne la reprends pas comme une consigne.** Les tentatives ultérieures ont démontré un agent SSH bloqué (`ssh-add` consommant presque tout le CPU), et `ssh -G github.com` affichait une configuration par défaut (port 22, sans clé personnalisée). Ce résultat ne sélectionnait pas automatiquement la bonne clé.

La procédure correcte :

1. Contrôler `git remote -v` (SSH ou HTTPS), `git status -sb` et `git log --oneline -3`.
2. Afficher la **configuration effective** : `ssh -G github.com | grep -E '^(hostname|port|identityfile|identityagent) '` ; cela ne prouve pas qu'une authentification réussit.
3. Tester, **sans deviner**, une identité explicite si elle a été vérifiée localement ; limiter le temps de connexion ; ne pas afficher le contenu de la clé privée.
4. Si un processus tourne en boucle, l'interrompre et traiter l'erreur avant le prochain push. Ne pas recréer des commits.
5. Vérifier le succès du push depuis GitHub ; ne pas considérer un silence du terminal comme une publication.

**État GitHub vérifié le 27/10 :** les commits `5d2f29e` et `d69d3a5`, qui étaient bloqués pendant les essais, sont désormais présents. Le dernier commit consulté est `c26fd6cb3` (*Add training environment templates*). C'est une observation du dépôt distant, **pas une explication supposée de la solution SSH locale**.

## 14. Débogage : le symptôme désigne la couche à examiner

| Symptomatique | Test sûr | Correction à envisager (pas automatique) |
|---|---|---|
| `ModuleNotFoundError` | `python -c 'import sys; print(sys.executable)'`; dans notebook idem | Changer de noyau/interpréteur ; ensuite installer dans le bon projet |
| `pip` installe mais Jupyter ne trouve rien | Comparer `sys.executable` terminal/notebook | Installer `ipykernel` dans la bonne `.venv`; choisir noyau |
| `uv sync` échoue | Lire `pyproject.toml`, `[tool.uv.workspace]`, chemins des membres | Réparer le projet sur branche dédiée ; ne pas toucher à la racine à l'aveugle |
| `uv run` remplace des paquets inattendus | Vérifier racine du workspace et `uv.lock` | Choisir projet correct ; comprendre sync automatique |
| `python` et `python3` diffèrent | `command -v python`, `command -v python3` | Invoquer `./.venv/bin/python` explicitement |
| Import de mauvais module | Vérifier qu'aucun fichier local ne s'appelle `requests.py`, `json.py`, `openai.py` | Renommer le fichier local après contrôle |
| Connexion PostgreSQL/Qdrant refusée | Vérifier URL, hôte, port, `docker ps`, santé des services | Corriger l'adresse ou démarrer le bon service, sans recréer les volumes |
| `localhost` fonctionne sur hôte mais pas dans n8n | Identifier si le client tourne dans Docker | Utiliser le DNS de service ou l'adresse d'hôte réellement accessible |
| Échec GPU / CUDA | Vérifier `nvidia-smi`, version Torch/vLLM et process actifs | Ne pas installer des versions concurrentes dans le serveur opérationnel |
| `git status` affiche des dossiers d'un autre exercice | `git rev-parse --show-toplevel` | Sélectionner les chemins du bon projet au moment de `git add` |
| `git push` reste silencieux | Voir processus SSH, authentification, vérification côté distant | Ne pas relancer 3 fois, ne pas inventer une clé |
| Un vrai secret apparaît dans un commit | Vérifier l'étendue de la divulgation | Révoquer la clé et traiter l'historique Git |

## 15. Trois exercices autonomes — 45 minutes chacun

### Exercice A — Construire un environnement propre sans aide (45 min)

**Sur `~/lab-python/etl-demo`, jamais directement sur `~/formation`.** Créer un projet `uv` avec Python 3.12, ajouter `requests` et `python-dotenv`, un groupe de développement avec `pytest`, exécuter un script affichant le chemin de Python et la version de `requests`. **Preuve attendue :** `pyproject.toml`, `uv.lock`, `.python-version`, README indiquant les commandes de reprise, capture de `sys.executable`. Expliquer pourquoi `.venv` n'est pas committée. Aucun service externe requis.

### Exercice B — Auditer un projet existant sans modification (45 min)

Comparer `~/formation/RAG/cours-rag` et `~/formation/N8N/B5_conseiller_produit_v2`. Relever : manifestes et versions Python déclarées, bibliothèques directes, services nécessaires, manière de charger `.env`, endroit où vit l'environnement, commande de lancement **documentée**. Relever trois informations manquantes pour une reproduction par une tierce personne. **Ne pas lancer `setup.sh`, `uv sync`, le serveur GPU ou Docker.**

### Exercice C — Simuler deux projets dans un Git indépendant (45 min)

Créer un **nouveau dossier hors `~/formation`**, initialiser Git et deux sous-dossiers `projet-a` et `projet-b`. Créer un README dans chacun, modifier seulement `projet-a`, lire `git status`, sélectionner avec `git add -- projet-a/README.md`, contrôler l'index puis committer. Refaire pour `projet-b`. Ajouter une règle `.gitignore` pour `.env` et `.venv/`. **Preuve attendue :** deux commits thématiques, aucune `.env` ni `.venv` suivie, capacité à expliquer pourquoi un dépôt Git peut contenir plusieurs projets sans les confondre.

## 16. Autotest : expliquer avant de consulter le corrigé

1. Quelle différence exacte entre `.env`, `.venv` et `.python-version` ?
2. Pourquoi `pip install` peut réussir dans un terminal puis `import` échouer dans un notebook ?
3. `pyproject.toml` donne `requests>=2.31` et `uv.lock` contient une version précise : qui fixe quoi ?
4. Quelle commande permet de retrouver l'interpréteur Python **réellement utilisé** ?
5. Pourquoi faut-il éviter `uv sync` automatiquement à la racine de `~/formation` ?
6. Quelle différence entre installer `qdrant-client` et démarrer Qdrant ?
7. Dans un conteneur n8n, `127.0.0.1` désigne-t-il ton Z4 ?
8. Que faut-il publier d'un projet Python fonctionnel ? Que faut-il exclure ?
9. Tu as modifié RAG et N8N, mais veux publier seulement N8N : comment sélectionner correctement ?
10. Pourquoi un `git commit` réussi ne signifie pas que GitHub possède le code ?
11. Un fichier déjà publié devient ignoré après modification de `.gitignore` : est-il supprimé du dépôt ?
12. Comment prouver qu'une installation fonctionne sur **une autre machine** et non seulement avec les dépendances accumulées sur ton Z4 ?

### Corrigé condensé

1. `.env` est une configuration ; `.venv` contient les paquets et l'interpréteur virtuel ; `.python-version` fixe une préférence de version Python.
2. Les deux utilisent probablement des interpréteurs différents ; comparer `sys.executable`.
3. Le manifeste décrit les contraintes directes ; le lockfile conserve la résolution exacte.
4. `python -c 'import sys; print(sys.executable)'` ; équivalent depuis la cellule notebook.
5. Le workspace racine contient plusieurs membres, dont certains chemins ne sont pas présents sur le GitHub public ; `uv sync` modifie aussi l'environnement et peut échouer.
6. `qdrant-client` est un client Python ; Qdrant est un service indépendant (souvent Docker).
7. Non, il désigne en général **le conteneur** dans lequel tourne la commande.
8. Code, tests, README, manifestes, lockfile, exemples anonymes ; exclure `.env`, `.venv`, poids, caches et données privées.
9. `git add -- N8N/nom_fichier` après contrôle ; `git diff --cached --name-status` avant le commit.
10. `git commit` écrit localement ; `git push` publie si l'accès et l'historique le permettent.
11. Non : ignorer n'annule pas les fichiers déjà suivis ; retirer le fichier de l'index est une action distincte.
12. Recréer dans un nouveau dossier/environnement depuis les manifestes et services documentés, exécuter les tests et consigner les résultats.

## 17. Routine de cinq minutes, à appliquer dès la prochaine séance

**Début :** `pwd` → `git rev-parse --show-toplevel` → `git status -sb` → `sys.executable` → lire le manifeste du sous-projet → vérifier les ports et services nécessaires.  
**Pendant :** travailler sur *un objectif* ; conserver les dépendances durables dans le bon manifeste ; noter les erreurs reproductibles ; distinguer travaux personnels et supports du professeur.  
**Fin :** exécuter un test, nettoyer les sorties confidentielles des notebooks, `git diff`, `git add` **ciblé**, vérifier `git diff --cached`, committer avec un message explicite ; confirmer le `push` côté GitHub.  
**Interdit par défaut :** `sudo pip install`, `git add .` à la racine, `git push --force`, `git reset --hard`, `docker compose down -v`, redémarrer des services LLM actifs sans inspection.

## 18. Sources contrôlées et documentation officielle

**Dépôt GitHub personnel consulté le 27/10/2026 :**
- Racine : `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/pyproject.toml` ; `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/.gitignore` ; `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/Created_enviroment_uv_version.txt`.
- RAG : `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/cours-rag/pyproject.toml`.
- B5 : `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/requirements.txt` ; `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md` ; `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/setup.sh`.
- n8n : `https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/env.example`.
- Cours déjà produit : *Cours personnel 10 — Git, GitHub et sauvegarde du travail*, complété ici pour les frontières entre environnements et projets ; sa section SSH est rectifiée §13.

**Règles générales vérifiées auprès des documentations officielles :**
- Python `venv` : `https://docs.python.org/3/library/venv.html`
- `uv` structure des projets : `https://docs.astral.sh/uv/concepts/projects/layout/`
- `uv` verrouillage et synchronisation : `https://docs.astral.sh/uv/concepts/projects/sync/`
- `uv` workspaces : `https://docs.astral.sh/uv/concepts/projects/workspaces/`
- `uv` versions de Python : `https://docs.astral.sh/uv/concepts/python-versions/`
- `uv` et Jupyter : `https://docs.astral.sh/uv/guides/integration/jupyter/`
- Git documentation : `https://git-scm.com/docs/`

**Principe de niveau :** les fichiers présents sur GitHub sont des preuves d'existence d'un travail, **pas des preuves de compétence indépendante**. La compétence « prouvée » nécessite reproduction manuelle, diagnostic explicable et résultat contrôlé.
