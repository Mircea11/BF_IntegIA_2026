# B.5 — Conseiller produit — Guide Z4 (VERSION 2)

**Cette archive a été créée pour cet exercice par ChatGPT. Elle n'est pas un document fourni par le formateur, ni un fichier déjà présent sur le Z4.**

**Pas de GitHub, pas de Gmail, pas d'envoi extérieur.** Le logiciel lit DummyJSON et l'API des modèles locaux. Le workflow n8n reste désactivé après import.

## Phase 0 — Télécharger (action manuelle indispensable)

1. Dans le chat, cliquer sur **Télécharger la version 2 — ZIP**.
2. Dans le navigateur Firefox du Z4, choisir **Enregistrer sous…** et sélectionner `/home/bm/Downloads`.
3. Dans un terminal Z4, vérifier :

```bash
ls -lh ~/Downloads/B5_conseiller_produit_Z4_v2.zip
```

Si `No such file or directory`, **arrêter**. Vérifier le dossier du téléchargement dans Firefox, ne pas exécuter la suite.

## Phase 1 — Décompresser et DIAGNOSTIQUER sans rien installer

```bash
cd ~
unzip -o ~/Downloads/B5_conseiller_produit_Z4_v2.zip -d ~
cd ~/B5_conseiller_produit_v2
bash preflight.sh
```

**Vérifier la sortie.** `A VERIFIER` veut dire que le service ou l'outil n'a pas répondu. Il n'est PAS encore question de changer le pare-feu ou de relancer dix services. Attention : Docker, Nemotron, BGE-M3 et accès DummyJSON sont indispensables avant la fin de l'exercice.

## Phase 2 — Installer un environnement Python + PostgreSQL/Qdrant (uniquement après vérification)

```bash
cd ~/B5_conseiller_produit_v2
bash setup.sh
```

Le mot de passe généré est stocké dans `.env` : ne pas publier ni copier ce fichier dans un dépôt.

Le script `setup.sh` : installe les dépendances dans `.venv` ; réutilise un Qdrant déjà accessible sur `127.0.0.1:6333` ou crée **b5-qdrant** ; crée/réutilise un conteneur **b5-postgres** isolé, sur `127.0.0.1:5433`, avec volume de données persistant. Il ne modifie pas le PostgreSQL de la formation. Nécessite Docker déjà utilisable sans sudo. En cas d'erreur Docker, **arrêter**, ne pas lancer des scripts de nettoyage.

## Phase 3 — Modèles IA déjà utilisés pendant la formation

La configuration retenue est celle de ton Z4 :
- Nemotron vLLM : `http://172.21.0.1:8000/v1`, modèle `veltis-llm`.
- BGE-M3 vLLM : `http://172.21.0.1:8001/v1`, modèle `bge-m3`.
- n8n dans Docker : `http://localhost:5678` côté navigateur.

**Ces adresses sont une hypothèse à vérifier dans `preflight.sh`, pas la preuve que des processus sont actifs.** Les modèles utilisent la VRAM ; **ne jamais relancer une instance déjà active**. Si les services sont absents, les démarrer dans des terminaux séparés où l'environnement `(vllm_server)` est activé.

Nemotron, si le port 8000 ne répond pas :

```bash
vllm serve /home/bm/models/nemotron3-nano-4b/vllm \
  --served-model-name veltis-llm --host 172.21.0.1 --port 8000 \
  --gpu-memory-utilization 0.50 --max-model-len 2048 \
  --max-num-seqs 1 --enforce-eager
```

BGE-M3, si le port 8001 ne répond pas :

```bash
vllm serve /home/bm/models/rag/embedder/bge-m3 \
  --runner pooling --served-model-name bge-m3 \
  --host 172.21.0.1 --port 8001 \
  --gpu-memory-utilization 0.20 --max-model-len 1024
```

Si l'un de ces démarrages échoue (VRAM, modèle absent, port occupé), **arrêter**. Ne pas changer plusieurs options simultanément. Les noms et chemins de modèles proviennent des précédents exercices ; ils restent à vérifier sur le Z4. Retester ensuite `bash preflight.sh`.

## Phase 4 — Démarrer le backend

Dans un terminal Z4 (à garder ouvert) :

```bash
cd ~/B5_conseiller_produit_v2
bash run.sh
```

Dans un deuxième terminal :

```bash
curl -fsS http://172.21.0.1:8765/health | python3 -m json.tool
```

Passer à la suite **uniquement si** `ready: true` et les quatre champs de `services` sont à `true`.

## Phase 5 — Indexer DEUX fois et comparer les résultats

```bash
curl -fsS -X POST http://172.21.0.1:8765/reindex | python3 -m json.tool
curl -fsS -X POST http://172.21.0.1:8765/reindex | python3 -m json.tool
```

Sur les données attendues de l'exercice : `source_count = 194`, `qdrant_count = 194`, puis à nouveau `194`. L'API peut changer ; si elle retourne un nombre différent, ne pas maquiller le résultat. Indexation peut prendre du temps : **attendre la réponse avant de lancer la seconde**.

## Phase 6 — Vérifier le chat AVANT n8n

Copier ce bloc complet dans un terminal Z4 :

```bash
python3 - <<'B5_TEST_CHAT'
import json, urllib.request
url = 'http://172.21.0.1:8765/chat'
questions = [
    "Je m'appelle Sam",
    "Comment je m'appelle ?",
    "Je cherche un smartphone Samsung à moins de 500 €",
    "Je voudrais un ballon de volley",
    "Quel est le meilleur restaurant de Bruxelles ?",
]
for question in questions:
    payload = json.dumps({'session_id':'b5-sam-check','message':question},ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=140) as resp:
        result = json.load(resp)
    print('QUESTION:', question)
    print('RÉPONSE :', result['answer'])
    print('---')
B5_TEST_CHAT
```

**Ce test doit confirmer** : le prénom Sam, pas de S8 en rupture comme disponible, une alternative au volley, refus du restaurant. Si une réponse est mauvaise, arrêter : ne pas ajouter n8n pour cacher l'erreur.

## Phase 7 — n8n (uniquement après réussite des tests du terminal)

1. Ouvrir n8n dans le navigateur : `http://localhost:5678`.
2. Importer le fichier `B5_REINDEX_n8n.json` depuis `~/B5_conseiller_produit_v2/` dans un workflow séparé, puis cliquer `Execute workflow`.
3. Importer `B5_CHAT_n8n.json` dans un autre workflow, puis cliquer `Test chat`.
4. Ne pas activer un webhook de chat public : le service local n'a pas d'authentification.

### Test manuel de la mémoire

1. Dans un chat n8n, saisir `Je m'appelle Sam`, puis `Comment je m'appelle ?`.
2. Garder le même chat / même session, redémarrer **n8n seulement** (ne pas supprimer ou redémarrer PostgreSQL).
3. Réouvrir la même session et redemander le prénom ; noter la réponse. Si n8n crée une nouvelle session, le test n'est pas équivalent. Pour la persistance de la base, le test `session_id` fixe du terminal est plus fiable.

## Tests unitaires (réponses simulées, pas les vrais services)

```bash
cd ~/B5_conseiller_produit_v2
source .venv/bin/activate
python test_b5.py
```

Ces tests valident des scénarios simulés. Ils ne remplacent **pas** les tests sur ton Z4, ni un vrai redémarrage de n8n avec sa session.

## Limites importantes

- DummyJSON expose `price` sans devise explicite dans les champs choisis. Le programme affiche le **prix numérique exact**, sans prétendre qu'il s'agit d'euros. Les requêtes « moins de 500 € » sont une comparaison numérique pour l'exercice, **pas une conversion**.
- Un produit dont le stock n'est pas vérifiable n'est pas proposé comme disponible.
- Le résultat de recherche sémantique doit être validé sur les vrais produits, surtout pour tennis, cuisine et alternatives.
- Ne pas ouvrir le port 8765 sur Internet : prototype sans authentification.
- Les modèles, leurs poids et leurs environnements ne sont **pas inclus dans le ZIP** ; le ZIP n'est pas un package autonome.
- Si une étape échoue, **arrêter** et relever son numéro et l'erreur. Ne pas supprimer de conteneurs, de volumes ou de fichiers.
