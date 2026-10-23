#!/usr/bin/env bash

# B.5 — Installation pour HP Z4
# Le script ne modifie ni Nemotron ni n8n.

# Arrêter immédiatement en cas d'erreur.
set -euo pipefail

# Se placer dans le dossier contenant ce script.
cd "$(dirname "${BASH_SOURCE[0]}")"

# Protéger les nouveaux fichiers privés.
umask 077


# ==========================================
# 1. VÉRIFICATION DES PRÉREQUIS
# ==========================================

# Vérifier que les programmes nécessaires existent.
for outil in docker curl python3 openssl; do
  command -v "$outil" >/dev/null 2>&1 || {
    echo "ERREUR : $outil est absent." >&2
    exit 1
  }
done

# Vérifier que Docker fonctionne.
docker info >/dev/null 2>&1 || {
  echo 'ERREUR : Docker inaccessible pour cet utilisateur.' >&2
  exit 1
}

# Vérifier que les fichiers Python du projet existent.
for fichier in app.py test_b5.py requirements.txt; do
  [ -f "$fichier" ] || {
    echo "ERREUR : fichier manquant : $fichier" >&2
    exit 1
  }
done

echo "OK : prérequis vérifiés."


# ==========================================
# 2. CONFIGURATION .env
# ==========================================

# Créer .env uniquement s'il n'existe pas.
if [ ! -f .env ]; then

  # Générer un mot de passe PostgreSQL.
  PG_PASS="$(openssl rand -hex 18)"

  # Écrire les paramètres de connexion.
  cat > .env <<EOF
PG_DSN=postgresql://b5user:${PG_PASS}@127.0.0.1:5433/b5shop
QDRANT_URL=http://127.0.0.1:6333
EMBED_URL=http://172.21.0.1:8001/v1
EMBED_MODEL=bge-m3
LLM_URL=http://172.21.0.1:8000/v1
LLM_MODEL=veltis-llm
DUMMYJSON_URL=https://dummyjson.com
EOF

  echo "OK : fichier .env créé."

else
  echo "OK : fichier .env existant conservé."
fi

# Seul ton utilisateur peut lire et modifier ce fichier.
chmod 600 .env


# ==========================================
# 3. LECTURE DU MOT DE PASSE POSTGRESQL
# ==========================================

# Utiliser Python au lieu de sed.
# Vérifier également l'adresse de la base.

PG_PASS="$(python3 - <<'PY'
from pathlib import Path
from urllib.parse import urlsplit, unquote

# Lire le fichier de configuration.
lines = Path('.env').read_text(
    encoding='utf-8'
).splitlines()

# Extraire PG_DSN.
values = [
    line.split('=', 1)[1].strip()
    for line in lines
    if line.startswith('PG_DSN=')
]

# Vérifier qu'une seule configuration existe.
if len(values) != 1:
    raise SystemExit(
        'ERREUR : PG_DSN doit apparaître une seule fois.'
    )

# Découper l'adresse PostgreSQL.
u = urlsplit(values[0])

# Vérifier utilisateur, adresse, port et base.
try:
    ok = (
        u.scheme == 'postgresql'
        and u.username == 'b5user'
        and u.hostname == '127.0.0.1'
        and u.port == 5433
        and u.path == '/b5shop'
        and bool(u.password)
    )
except ValueError:
    ok = False

if not ok:
    raise SystemExit(
        'ERREUR : PG_DSN incompatible avec B.5.'
    )

# Retourner le mot de passe à Bash.
print(unquote(u.password))
PY
)"

# Refuser un mot de passe vide.
[ -n "$PG_PASS" ] || {
  echo 'ERREUR : mot de passe PostgreSQL vide.' >&2
  exit 1
}

echo "OK : configuration PostgreSQL validée."


# ==========================================
# 4. POSTGRESQL
# ==========================================

# Vérifier si le conteneur b5-postgres existe.
if docker container inspect b5-postgres >/dev/null 2>&1; then

  # Vérifier s'il fonctionne déjà.
  if [ "$(docker inspect -f '{{.State.Running}}' b5-postgres)" = 'true' ]; then

    echo "OK : b5-postgres fonctionne déjà."

  else

    # Démarrer le conteneur existant.
    docker start b5-postgres >/dev/null

    echo "OK : b5-postgres redémarré."

  fi

else

  # Créer PostgreSQL seulement si nécessaire.
  docker run -d \
    --name b5-postgres \
    -e POSTGRES_USER=b5user \
    -e POSTGRES_PASSWORD="$PG_PASS" \
    -e POSTGRES_DB=b5shop \
    -v b5_postgres_data:/var/lib/postgresql/data \
    -p 127.0.0.1:5433:5432 \
    postgres:16-alpine >/dev/null

  echo "OK : PostgreSQL B.5 créé."

fi


# ==========================================
# 5. QDRANT
# ==========================================

# Réutiliser Qdrant s'il répond déjà sur 6333.
if curl -fsS --max-time 4 \
  http://127.0.0.1:6333/healthz \
  >/dev/null 2>&1; then

  echo "OK : Qdrant existant réutilisé."

# Sinon, vérifier le conteneur B.5.
elif docker container inspect b5-qdrant >/dev/null 2>&1; then

  # Si le conteneur fonctionne mais ne répond pas,
  # arrêter plutôt que le redémarrer aveuglément.
  if [ "$(docker inspect -f '{{.State.Running}}' b5-qdrant)" = 'true' ]; then
    echo "ERREUR : Qdrant fonctionne mais ne répond pas." >&2
    exit 1
  fi

  # Démarrer le conteneur existant.
  docker start b5-qdrant >/dev/null 2>&1 || {
    echo "ERREUR : impossible de démarrer Qdrant." >&2
    exit 1
  }

  echo "OK : Qdrant redémarré."

else

  # Créer Qdrant si aucun serveur utilisable n'existe.
  docker run -d \
    --name b5-qdrant \
    -p 127.0.0.1:6333:6333 \
    -v b5_qdrant_data:/qdrant/storage \
    qdrant/qdrant:latest >/dev/null

  echo "OK : Qdrant créé."

fi


# ==========================================
# 6. ENVIRONNEMENT PYTHON
# ==========================================

# Créer un environnement Python propre à B.5.
python3 -m venv .venv || {
  echo "ERREUR : impossible de créer .venv." >&2
  echo "Vérifier que python3-venv est installé." >&2
  exit 1
}

# Activer cet environnement.
. .venv/bin/activate

# Installer les dépendances.
python -m pip install -r requirements.txt

# Vérifier la syntaxe Python.
python -m py_compile app.py test_b5.py

echo "OK : environnement Python installé."


# ==========================================
# 7. VÉRIFICATIONS FINALES
# ==========================================

# Attendre que PostgreSQL réponde.
for ((i=1; i<=15; i++)); do

  if docker exec b5-postgres \
    pg_isready -U b5user -d b5shop \
    >/dev/null 2>&1; then
    break
  fi

  sleep 2
done

# Confirmer que PostgreSQL répond.
docker exec b5-postgres \
  pg_isready -U b5user -d b5shop \
  >/dev/null 2>&1 || {
    echo "ERREUR : PostgreSQL ne répond pas." >&2
    exit 1
  }


# Attendre que Qdrant réponde.
for ((i=1; i<=15; i++)); do

  if curl -fsS --max-time 3 \
    http://127.0.0.1:6333/healthz \
    >/dev/null 2>&1; then
    break
  fi

  sleep 2
done

# Confirmer que Qdrant répond.
curl -fsS --max-time 3 \
  http://127.0.0.1:6333/healthz \
  >/dev/null || {
    echo "ERREUR : Qdrant ne répond pas." >&2
    exit 1
  }


# Tester une véritable connexion PostgreSQL.
# pg_isready seul ne vérifie pas le mot de passe.

python - <<'PY'
import os
from pathlib import Path
from psycopg import connect
from dotenv import load_dotenv

# Charger les paramètres du projet.
load_dotenv(Path('.env'), override=True)

# Se connecter à PostgreSQL.
with connect(
    os.environ['PG_DSN'],
    connect_timeout=8
) as db:

    # Exécuter une requête simple.
    with db.cursor() as cur:
        cur.execute('SELECT 1')
        assert cur.fetchone()[0] == 1

print("OK : connexion PostgreSQL validée.")
PY


# ==========================================
# TERMINÉ
# ==========================================

echo ""
echo "INSTALLATION B.5 TERMINÉE."
echo "Nemotron et n8n non modifiés."
echo "BGE-M3 reste à vérifier séparément."
echo "Prochaine commande : bash preflight.sh"

