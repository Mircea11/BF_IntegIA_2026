# Astral UV

Documentation officielle : <https://docs.astral.sh/uv/>

## A quoi ca sert

- Gerer Python, les environnements virtuels et les dependances.
- Remplacer le trio `venv` + `pip` + `requirements.txt` dans beaucoup de cas.
- Standard recommande pour les projets Python de cette formation.

## 1. Installation

Doc officielle : <https://docs.astral.sh/uv/getting-started/installation/>

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

### Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

### Verifier Python gere par uv

```bash
uv python list
```

## 2. uv venv

Doc officielle : <https://docs.astral.sh/uv/pip/environments/#creating-a-virtual-environment>

- Cree un environnement virtuel Python.
- Utiliser `uv venv` au debut d'un projet ou quand on veut un environnement propre.

### Creer un environnement

```bash
uv venv
```

### Forcer un nom de dossier

```bash
uv venv .venv
```

### Choisir une version de Python

```bash
uv venv --python 3.12
```

### Activer l'environnement

Windows PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Linux :

```bash
source .venv/bin/activate
```

## 3. uv python

Doc officielle : <https://docs.astral.sh/uv/concepts/python-versions/>

- Permet de lister, installer et gerer differentes versions de Python.
- Pratique pour standardiser une version sur toutes les machines.

### Voir les versions disponibles

```bash
uv python list
```

### Installer une version precise

```bash
uv python install 3.12
```

### Installer plusieurs versions

```bash
uv python install 3.11 3.12
```

### Verifier le Python utilise dans le projet

```bash
uv run python --version
```

## 4. uv init, uv.lock et pyproject.toml

Doc officielle : <https://docs.astral.sh/uv/guides/projects/>

### Initialiser un projet

```bash
uv init mon_projet
cd mon_projet
```

### Initialiser dans le dossier courant

```bash
uv init
```

### Ce que fait uv init

- Cree un projet Python gere par `uv`.
- Cree `pyproject.toml`.
- Initialise aussi un depot Git dans le projet.
- Peut creer une structure minimale de projet selon le contexte.
- Prepare le projet pour `uv add`, `uv run` et `uv sync`.

### pyproject.toml

Doc officielle : <https://docs.astral.sh/uv/concepts/projects/layout/>

- Fichier de configuration du projet.
- Contient les metadonnees du projet.
- Contient les dependances declarees.
- C'est l'intention du projet.

Exemple minimal :

```toml
[project]
name = "mon-projet"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "requests>=2.32.0",
]
```

### uv.lock

Doc officielle : <https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile>

- Fichier de lock genere par `uv`.
- Contient les versions exactes resolues.
- Verrouille aussi les dependances transitives.
- Sert a reconstruire le meme environnement sur une autre machine.

### Difference rapide

- `pyproject.toml` : ce que le projet demande.
- `uv.lock` : ce que `uv` a resolu exactement.

## 5. uv add vs uv pip install

Doc officielle :

- `uv add` : <https://docs.astral.sh/uv/guides/projects/#adding-dependencies>
- `uv pip` : <https://docs.astral.sh/uv/pip/>

### uv add

- A utiliser dans un projet `uv`.
- Met a jour `pyproject.toml`.
- Met a jour `uv.lock`.
- Garde un projet reproductible.

```bash
uv add requests
```

```bash
uv add fastapi sqlalchemy
```

```bash
uv add --dev pytest ruff
```

### uv pip install

- Compatible avec l'approche `pip`.
- Installe dans un environnement existant.
- Ne gere pas le projet aussi proprement que `uv add`.

```bash
uv pip install requests
```

```bash
uv pip install -r requirements.txt
```

### Regle simple

- Projet moderne avec `uv` : preferer `uv add`.
- Besoin ponctuel ou compatibilite `pip` : utiliser `uv pip install`.

## 6. uv sync

Doc officielle : <https://docs.astral.sh/uv/guides/projects/#syncing-the-environment>

- Synchronise l'environnement avec `pyproject.toml` et `uv.lock`.
- Installe ce qui manque.
- Supprime les ecarts avec l'etat attendu du projet.

### Synchroniser

```bash
uv sync
```

### Inclure les dependances de developpement

```bash
uv sync --dev
```

### Quand l'utiliser

- Apres un `git clone`.
- Apres un `git pull`.
- Apres un `uv add`.
- Quand l'environnement local ne correspond plus au projet.

## Workflow de base

Doc officielle : <https://docs.astral.sh/uv/guides/projects/>

```bash
uv init mon_projet
cd mon_projet
uv venv
uv add requests
uv add --dev pytest
uv sync
```

### Lancer une commande dans le projet

```bash
uv run python main.py
```

Doc `uv run` : <https://docs.astral.sh/uv/guides/projects/#running-commands>

## Pieges frequents

- Confondre `pyproject.toml` et `uv.lock`.
- Utiliser `uv pip install` au lieu de `uv add` dans un projet `uv`.
- Oublier `uv sync` apres recuperation ou changement de dependances.
- Penser qu'un package installe avec `uv pip install` est automatiquement declare dans le projet.

## A retenir

- `uv init` initialise le projet.
- `uv venv` cree l'environnement virtuel.
- `uv add` ajoute proprement les dependances.
- `uv.lock` verrouille les versions exactes.
- `uv sync` remet l'environnement dans l'etat attendu.
