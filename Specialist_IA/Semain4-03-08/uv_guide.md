# Guide UV — Environnement de développement Python

> **UV** est un gestionnaire de paquets et d'environnements Python ultra-rapide, écrit en Rust.

---

## Explications des étapes

### 1. Installation de UV

#### Windows (PowerShell — Execution Policy Bypass)

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Vérifier l'installation

```bash
uv --version
```

---

### 2. Initialiser un projet — `uv init`

Crée la structure de base d'un nouveau projet Python :

```bash
uv init mon-projet
```

> Génère un fichier `pyproject.toml`, un `README.md` et un dossier `src/` prêts à l'emploi.

---

### 3. Accéder au dossier du projet

```bash
cd mon-projet
```

---

### 4. Créer un environnement virtuel — `uv venv`

Crée un environnement virtuel `.venv` dans le répertoire courant :

Spécifier une version de Python :

```bash
uv venv --python 3.12
```

---

### 5. Activer l'environnement virtuel

**Windows (PowerShell — Execution Policy Bypass) :**

```powershell
powershell -ExecutionPolicy Bypass -File ".venv\Scripts\Activate.ps1"
```

Ou, si l'Execution Policy est déjà définie pour la session :

```powershell
# Autoriser les scripts pour la session courante
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Puis activer
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux :**

```bash
source .venv/bin/activate
```

---

### 6. Ajouter des dépendances — `uv add`

Ajouter un paquet au projet :

```bash
uv add requests
```

Ajouter plusieurs paquets en une seule commande :

```bash
uv add fastapi uvicorn sqlalchemy
```

Ajouter une version spécifique :

```bash
uv add "django>=5.0,<6.0"
```

Ajouter une dépendance de développement uniquement :

```bash
uv add --dev pytest ruff black
```

> Les dépendances sont automatiquement ajoutées dans le `pyproject.toml` et installées dans le `.venv`.

---

## Flux de travail complet (exemple)

```powershell
# 1. Installer UV
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Initialiser le projet
uv init mon-projet

# 3. Accéder au dossier
cd mon-projet

# 4. Créer l'environnement virtuel
uv venv --python 3.12

# 5. Activer l'environnement (Execution Policy Bypass)
powershell -ExecutionPolicy Bypass -File ".venv\Scripts\Activate.ps1"

# 6. Ajouter les dépendances
uv add notebook numpy
uv add --dev pytest ruff
```

---

## Références

- Documentation officielle : [https://docs.astral.sh/uv](https://docs.astral.sh/uv)
- Dépôt GitHub : [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
