#!/usr/bin/env bash
# Lecture seule : aucun conteneur ou service créé/modifié.
set -u
cd "$(dirname "$0")"
check() {
  label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf 'OK      %s\n' "$label"; else printf 'A VERIFIER  %s\n' "$label"; fi
}
check 'Python 3' python3 --version
check 'Docker accessible' docker info
check 'curl installé' command -v curl
check 'Accès réseau local Z4 (172.21.0.1)' sh -c "ip -4 -o addr show | grep -Fq ' 172.21.0.1/'"
check 'Nemotron (port 8000)' curl --fail --silent --max-time 5 http://172.21.0.1:8000/v1/models
check 'BGE-M3 (port 8001)' curl --fail --silent --max-time 5 http://172.21.0.1:8001/v1/models
check 'DummyJSON accessible' curl --fail --silent --max-time 10 https://dummyjson.com/products/1
check 'Qdrant (port 6333 ; optionnel avant setup)' curl --fail --silent --max-time 5 http://127.0.0.1:6333/healthz
printf '\nA VERIFIER = ne pas deviner. Corriger le service avant de passer au chat.\n'
