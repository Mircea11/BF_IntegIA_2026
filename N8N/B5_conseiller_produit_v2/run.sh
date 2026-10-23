#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] || { echo 'ERREUR: environnement absent. Exécuter d’abord bash setup.sh.' >&2; exit 1; }
BIND_HOST="${B5_BIND_HOST:-172.21.0.1}"
if ! ip -4 -o addr show 2>/dev/null | grep -Fq " $BIND_HOST/"; then
  echo "ERREUR: interface $BIND_HOST absente. Voir bash preflight.sh ; ne pas utiliser 0.0.0.0 sans protection." >&2
  exit 1
fi
. .venv/bin/activate
exec uvicorn app:app --host "$BIND_HOST" --port 8765
