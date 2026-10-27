# Cours personnel 13 — Docker : comprendre, connecter et protéger tes services IA

**Formation AI Integration Specialist · Consolidation personnelle · 26 octobre 2026**  
**Support du collègue :** `2026-09-22 - Docker.md`, tiré de `2026 Cours.zip`. Module attribué dans cette synthèse à Gavin Chaineux, 22 septembre 2026.  
**Références personnelles vérifiées :** dépôt GitHub `Mircea11/BF_IntegIA_2026`, fichiers `formation/docker-httpd/docker-compose.yaml`, `N8N/docker-compose.yml.save`, `N8N/B5_conseiller_produit_v2/setup.sh` et `README_SETUP_FR.md` ; échanges et diagnostic du projet B5.  
**Limite des sources :** le support original « Docker v2-5.pdf » cité par ton collègue n'a pas été retrouvé dans les fichiers consultés. Nous utilisons sa synthèse, les fichiers effectivement présents dans ton dépôt et la documentation Docker. L'état **actuel** des conteneurs sur le Z4 doit être vérifié sur place.  
**Durée conseillée :** 70–90 minutes de lecture + trois blocs autonomes de 45 minutes.  
**But :** expliquer ce qui tourne où, identifier les données à préserver, comprendre les accès réseau et diagnostiquer des erreurs sans détruire les conteneurs ni leurs volumes.

> **Niveau de preuve.** « Présent sur GitHub » = code ou configuration observables ; « exécuté pendant la formation » = activité rapportée dans nos échanges ; « maîtrisé seul » = à vérifier par les exercices. Une configuration archivée n'est pas nécessairement celle qui tourne aujourd'hui.

## 1. La carte de TON système avant la théorie

Le conseiller produit B5 et les exercices RAG réunissent plusieurs programmes. Certains sont des conteneurs ; les serveurs vLLM ont été lancés sur Ubuntu, dans ton environnement Python. Il ne faut pas les confondre.

```text
HP Z4 sous Ubuntu (machine hôte)
 |
 |-- Docker Engine
 |    |-- n8n : interface et orchestration (hôte :5678)
 |    |-- PostgreSQL : conversations / données persistantes
 |    |-- Qdrant : index de vecteurs, collection B5
 |    '-- réseaux Docker + volumes nommés
 |
 |-- Python / vLLM sur l'hôte (selon ta configuration)
 |    |-- Nemotron : API texte, port 8000
 |    '-- BGE-M3 : API embeddings, port 8001
 |
 '-- navigateur / terminal / scripts Python
      '-- n8n et l'application B5 sollicitent ces services
```

Le `README_SETUP_FR.md` de B5 documente un serveur `veltis-llm` à `172.21.0.1:8000`, un modèle `bge-m3` à `172.21.0.1:8001`, Qdrant sur `127.0.0.1:6333` et une base B5 isolée sur `127.0.0.1:5433`. **Ce sont des adresses de configuration à contrôler**, pas la preuve que les services répondent actuellement.

**Question centrale :** quand le formulaire n8n demande « Je voudrais un ballon de volley », quelle partie assure le dialogue, la recherche, le stock, l'historique et la réponse ? Dessine les cinq flèches sans regarder le diagramme.

## 2. Conteneurs, machines virtuelles et processus Linux

Une **machine virtuelle** embarque un système invité et son noyau ; un **conteneur Linux** isole des processus qui partagent le noyau de l'hôte. Les mécanismes Linux importants sont les *namespaces* (vue isolée des ressources) et les *cgroups* (comptabilisation/limitation des ressources).

| Notion | Définition utile | Dans ton cas |
|---|---|---|
| Image | Ensemble de couches et de paramètres servant de modèle | `postgres:16`, `qdrant/qdrant`, image n8n |
| Conteneur | Instance d'une image, avec son propre système de fichiers modifiable | Conteneur n8n ou PostgreSQL |
| Docker Engine | Service qui construit et exécute les conteneurs | Démon `dockerd` sur Ubuntu |
| Dockerfile | Recette de construction d'une image | Pas obligatoire si une image publique convient |
| Compose | Description YAML d'une application multi-conteneurs | n8n + PostgreSQL ; Ollama + Open WebUI |
| Volume | Stockage indépendant du cycle de vie du conteneur | Historique PostgreSQL, configuration n8n, index Qdrant |
| Bind mount | Dossier local rendu accessible dans le conteneur | `./data:/data` dans le fichier n8n archivé |

**À retenir :** une image peut être reconstruite ou retéléchargée ; **tes données** ne le peuvent pas toujours. Les volumes sont persistants, mais ne sont **pas une sauvegarde externe**. L'isolation Docker n'a pas la même portée de sécurité que l'isolation d'une VM.

## 3. Lire les commandes avant de les exécuter

### Les commandes de diagnostic autorisées pour ce cours

```bash
# Version et disponibilité du moteur
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'

# Ce qui existe aujourd'hui
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker ps -a --format 'table {{.Names}}\t{{.Status}}'
docker volume ls
docker network ls

# Lire les détails d'un conteneur CONNU (adapter le nom)
docker inspect --format '{{json .Mounts}}' n8n-n8n-1
```

Si `n8n-n8n-1` n'existe plus, **ne le recrée pas** : récupère son nom dans `docker ps -a`. Les commandes ci-dessus sont destinées à la lecture ; elles n'installent rien. Les informations détaillées d'`inspect` peuvent toutefois contenir des secrets : ne copie pas la sortie intégrale sur un dépôt public.

### Comprendre `docker run`

```bash
# EXEMPLE THÉORIQUE — ne pas exécuter sur le système existant
# docker run -d --name exemple -p 127.0.0.1:8088:80 nginx:stable-alpine
```

`-d` = arrière-plan ; `--name` = nom ; `-p IP_HÔTE:PORT_HÔTE:PORT_CONTENEUR` = publication d'un port ; `-v source:destination` = montage ; `-e` = variable d'environnement. Dans un `Dockerfile`, `EXPOSE 80` **documente** un port ; ce n'est pas l'équivalent de `-p`.

### Commandes à NE PAS lancer comme exercices

`docker system prune -a`, `docker volume prune`, `docker compose down -v`, `docker rm`, `docker rmi` et `docker compose up -d` sur ton projet actif. Les premières peuvent supprimer des ressources ; la dernière peut recréer des services et provoquer une interruption si le Compose ou ses variables ont changé.

## 4. Docker Compose : lire tes fichiers comme une architecture

Le fichier réel de ton dépôt `formation/docker-httpd/docker-compose.yaml` définit `ollama` et `webui` :

```yaml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama:/root/.ollama
    ports:
      - "11434:11434"
  webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
volumes:
  ollama:
  openwebui:
```

C'est un **extrait pédagogique fidèle aux paramètres essentiels**, pas une copie complète du fichier. Ici, le navigateur atteint l'interface sur `localhost:3000`. Depuis `webui`, le serveur Ollama est joint par son **nom de service** `ollama` sur le port **interne** 11434. `localhost:11434` à l'intérieur de `webui` désignerait `webui` lui-même.

Le fichier archivé `N8N/docker-compose.yml.save` donne un second exemple : `postgres` et `n8n`, `DB_POSTGRESDB_HOST=postgres`, volumes `db_storage`, `n8n_storage` et montage `./data:/data`. Il déclare une condition `depends_on: service_healthy` avec un `healthcheck` PostgreSQL.

**Attention :** ce fichier archivé comporte une ligne placée de façon incohérente après la section `volumes:`. On ne doit **pas** le traiter comme une configuration de production vérifiée ni l'exécuter sans validation. Le fichier réellement utilisé sur le Z4 peut différer.

### `depends_on` n'est pas une garantie générale

`depends_on: - ollama` impose l'ordre de démarrage, mais pas la disponibilité de l'API. Avec un `healthcheck` et `condition: service_healthy`, Compose peut attendre une condition de santé définie. Cela ne remplace pas les tests fonctionnels. Dans B5, la vraie preuve reste un `GET /health` et un appel métier réussi.

## 5. Le réseau Docker : l'origine de nombreuses pannes n8n/vLLM

Trois points de vue à distinguer :

| Lieu où tourne la commande | `localhost` désigne | Exemple d'adresse pertinente |
|---|---|---|
| Navigateur sur le HP Z4 | Le HP Z4 | `http://localhost:5678` vers le port publié de n8n |
| Conteneur n8n | Le conteneur n8n | `http://postgres:5432` **si** même réseau Compose |
| Python / vLLM sur l'hôte | Le HP Z4 | `http://127.0.0.1:8000`, selon liaison serveur |

Tu as utilisé `172.21.0.1` pour joindre depuis Docker les APIs vLLM exécutées sur l'hôte. Cette adresse peut correspondre à une interface de pont Docker de **ta** configuration ; elle n'est pas universelle et peut changer. Elle n'est correcte que si le serveur écoute sur cette interface et que le conteneur sait la joindre.

### Chemin de diagnostic progressif — sans changer le système

1. `docker ps` : le conteneur est-il actif ?
2. `docker port n8n-n8n-1` : quels ports sont publiés ? (adapter son vrai nom)
3. Depuis l'hôte : `curl --max-time 3 -I http://127.0.0.1:5678`.
4. Depuis l'hôte : `curl --max-time 3 http://127.0.0.1:8000/v1/models` si Nemotron est censé écouter sur localhost ; sinon utiliser son interface réelle.
5. Vérifier les réseaux via `docker network ls` et `docker inspect --format '{{json .NetworkSettings.Networks}}' NOM`.
6. **Seulement ensuite** tester la connectivité depuis le conteneur avec un outil déjà disponible ; ne pas installer de paquets dans n8n juste pour un test.

**Conflit possible :** `N8N/docker-compose.yml.save` publie PostgreSQL sur `5433:5432`, et le script `setup.sh` de B5 utilise `127.0.0.1:5433:5432` pour une base indépendante. Deux services ne peuvent pas publier simultanément la même combinaison adresse/port sur l'hôte. C'est une *collision potentielle de configuration*, pas la preuve d'une panne actuelle.

## 6. Volumes et persistance : pourquoi GitHub ne suffit pas

Ton dépôt GitHub contient du **code**, des notebooks et des configurations. Il ne sauvegarde pas automatiquement les **tables PostgreSQL**, les données de n8n ou les **vecteurs Qdrant**.

| Élément à protéger | Où sont les données ? | Preuve de sauvegarde nécessaire |
|---|---|---|
| n8n | Base et volume de configuration | Export de workflows + volume/base + clé de chiffrement protégée |
| PostgreSQL | Volume de données du conteneur | Dump cohérent + restauration de test |
| Qdrant | Stockage des collections | Snapshot/export selon installation + test de restauration |
| Configurations | Fichiers Compose, scripts, variables | Git pour fichiers non secrets ; copie protégée des secrets |
| Modèles IA | Poids locaux et caches | Inventaire, possibilité de retélécharger, vérification de versions |

Le collègue note correctement que les volumes survivent au retrait du conteneur ; attention toutefois : **`docker compose down -v` demande la suppression des volumes déclarés**. Et un volume conservé sur un disque unique reste vulnérable à une panne de disque. Pour PostgreSQL en activité, préfère un dump cohérent à une simple copie improvisée des fichiers bruts.

### Deux commandes de contrôle sans risque

```bash
docker volume ls
# Remplacer par le nom vraiment observé dans docker volume ls :
docker volume inspect NOM_DU_VOLUME
```

**Ne confonds pas** `postgres:16` (image), `b5-postgres` (conteneur possible), `b5_postgres_data` (volume possible) et `b5shop` (base logique) : quatre éléments différents. Le script B5 nomme ces ressources, mais une exécution réelle doit être vérifiée.

## 7. Dockerfile, build et fichiers à exclure

L'exemple du collègue décrit `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE`, `CMD` et `ENTRYPOINT`. Pour notre programme, l'important est l'ordre des couches : installer les dépendances **avant** de copier le code qui change souvent, afin de réutiliser le cache de build.

```dockerfile
# ILLUSTRATION : ne crée pas de service dans ce cours
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8765
CMD ["python", "app.py"]
```

La commande exacte dépend de l'application : le `app.py` de B5 utilise FastAPI et doit normalement être démarré par un serveur ASGI configuré, pas nécessairement par `python app.py`. **L'exemple montre la syntaxe Dockerfile, pas une recette exécutable de B5**. Un `.dockerignore` est distinct de `.gitignore` ; il empêche le transfert au *contexte de build* des `.env`, poids IA, caches et archives inutiles.

## 8. Sécurité : quatre risques concrets pour ton portfolio

1. **Dépôt public :** jamais de mots de passe, token, certificat ou `.env` dans Git. Le `2026-09-22 - Docker.md` du collègue signale un mot de passe probablement réel dans un fichier Compose historique ; je n'ai pas confirmé cette occurrence précise dans les fichiers actuels consultés. Si elle a été publiée, considère-la compromise, change la valeur concernée et analyse l'historique Git.
2. **Variables d'environnement :** utiliser `${POSTGRES_PASSWORD}` évite le mot de passe *en clair dans le YAML*, mais ne constitue pas une solution de gestion des secrets. `docker inspect` et `docker compose config` peuvent révéler des valeurs résolues. Évite de publier leurs sorties ; étudie les secrets Docker pour les déploiements.
3. **Ports :** publier `5678:5678`, `6333:6333` ou `11434:11434` sans adresse explicite peut rendre le service accessible au réseau. Utiliser `127.0.0.1:PORT:PORT` quand aucun accès extérieur n'est nécessaire.
4. **Interface Ollama/Open WebUI :** le fichier de démonstration a `WEBUI_AUTH=false`. C'est acceptable pour un laboratoire local contrôlé, **pas** pour un accès réseau non protégé.

**À ajouter à tes réflexes :** ne jamais coller les sorties de `.env`, `docker inspect` complet, `docker compose config` complet ou `docker logs` contenant des données clients dans GitHub. Préférer les diagnostics ciblés et expurgés.

## 9. Table de dépannage — symptômes rencontrés ou plausibles sur le Z4

| Symptôme | Interprétation à tester | Première vérification sûre |
|---|---|---|
| `connection refused` vers `8001` | BGE-M3 arrêté, mauvais bind ou port | `curl --max-time 3 http://ADRESSE:8001/v1/models` |
| `localhost` fonctionne sur Ubuntu mais pas dans n8n | Mauvais contexte réseau / conteneur | Comparer adresses hôte et conteneur |
| PostgreSQL répond mais mémoire perdue | Nouvelle session, nouvelle base ou mauvais volume | `docker ps -a` + montages + identifiant de session |
| `port is already allocated` | Deux services réclament le même port hôte | `docker ps --format ...` et `docker port NOM` |
| n8n démarre avant PostgreSQL | La base n'est pas encore prête | Santé DB / `depends_on: service_healthy` |
| Qdrant a zéro point après redémarrage | Mauvais volume, collection ou réindexation non lancée | Nom du volume, nom collection, count read-only |
| GPU saturé lorsque Nemotron et BGE-M3 tournent | Deux services partagent la VRAM | `nvidia-smi` (sur l'hôte), logs ciblés |
| GitHub contient le workflow mais pas le chat | Code sauvegardé ≠ base sauvegardée | Inventaire des volumes + stratégie de sauvegarde |

Les symptômes listés sont des **hypothèses diagnostiques**, pas tous des incidents prouvés dans ton historique.

## 10. Trois exercices d'autonomie, sans risque pour l'environnement actuel

### Bloc A — 45 min : inventaire exact du Z4

**Sans IA d'abord.** Exécute `docker ps`, `docker ps -a`, `docker volume ls` et `docker network ls`. Dans un tableau papier, associe chaque conteneur à : image, fonction, port publié, réseau, volume(s). Complète une case « inconnu » quand tu n'as pas la preuve.

**Livrable :** un schéma de ton système en 12 lignes au maximum. **Critère de réussite :** tu sais montrer où résident n8n, PostgreSQL, Qdrant et les deux services vLLM, sans confondre le réseau Docker et l'API du modèle. Ne partage pas de secrets.

### Bloc B — 45 min : audit de deux Compose, en lecture seule

Ouvre dans un éditeur les fichiers `formation/docker-httpd/docker-compose.yaml` et `N8N/docker-compose.yml.save` du dépôt local. Pour chacun, repère : les `services`, les images, `ports`, `volumes`, `depends_on`, les variables. Compare ce que raconte le fichier avec `docker ps` : une configuration sur GitHub ne prouve pas qu'elle est déployée.

**Option de validation syntaxique ciblée** (ne démarre rien) :

```bash
cd ~/formation
# Ce fichier de cours est un exemple ; validation seulement :
docker compose -f formation/docker-httpd/docker-compose.yaml config --quiet
```

Le fichier n8n `.save` n'est **pas** à lancer ; si tu souhaites l'étudier, relève d'abord sa ligne mal placée. **Critère :** expliquer correctement `3000:8080`, `OLLAMA_BASE_URL=http://ollama:11434` et `depends_on`.

### Bloc C — 45 min : enquête de persistance et plan de sauvegarde

Choisis **un seul** service (PostgreSQL B5, PostgreSQL n8n ou Qdrant). Sans modifier le service, retrouve le volume qui contient ses données. Note trois risques : suppression accidentelle du volume, perte du disque, absence de sauvegarde de cohérence. Écris une mini-procédure : *identifier → sauvegarder → protéger → restaurer sur une instance de test → prouver le résultat*. Le laboratoire s'arrête **avant** toute sauvegarde ou restauration réelle, qui nécessite un plan adapté à la base.

**Critère :** pouvoir expliquer pourquoi « GitHub à jour » ne prouve pas la récupérabilité des conversations B5 après une panne du Z4.

### Échelle de compétence à utiliser

| Niveau | Preuve attendue |
|---|---|
| R — Reconnu | Tu identifies Docker, Compose, volume et port sur un exemple |
| G — Avec guidage | Tu interprètes les commandes et les fichiers en suivant ce cours |
| A — Autonome | Tu construis seul l'inventaire et diagnostiques un port inaccessible |
| P — Prouvé | Tu documentes un service fonctionnel et une restauration effectivement testée |

## 11. Autotest — répondre avant de consulter le corrigé

1. Une image et un conteneur sont-ils la même chose ?
2. Pourquoi les conteneurs Linux partagent-ils le noyau de l'hôte ?
3. Que signifie `127.0.0.1:5433:5432` ?
4. Depuis le conteneur `webui`, à quoi renvoie `localhost` ?
5. Pourquoi `OLLAMA_BASE_URL=http://ollama:11434` fonctionne-t-il dans Compose ?
6. Que garantit `depends_on` sans healthcheck ?
7. Quelle différence entre volume nommé et bind mount ?
8. Est-ce que `EXPOSE 8000` publie le port sur l'ordinateur ?
9. Est-ce que `git push` sauvegarde les données PostgreSQL ou Qdrant ?
10. Pourquoi `docker compose down -v` est-il dangereux ?
11. Pourquoi `docker compose config --quiet` convient-il mieux à un audit partagé que `docker compose config` ?
12. Dans ton B5, qui fabrique les embeddings et qui effectue la recherche vectorielle ?

### Corrigé succinct

1. Non : image = modèle ; conteneur = instance. 2. Pour exécuter des processus isolés sans démarrer un noyau invité complet. 3. Port 5433 de l'hôte (interface loopback) vers 5432 du conteneur. 4. À `webui` lui-même. 5. Résolution DNS du service `ollama` sur le réseau Compose. 6. Ordre de démarrage, pas disponibilité applicative. 7. Volume géré par Docker, bind mount lié à un chemin hôte. 8. Non, `-p` / `ports:` publie. 9. Non, seulement les fichiers versionnés. 10. Elle demande la suppression des volumes déclarés. 11. Elle vérifie sans afficher les valeurs résolues potentiellement sensibles. 12. BGE-M3 produit des vecteurs ; Qdrant les indexe/interroge.

## 12. Références exactes et parcours de lecture

**Synthèse du collègue (fichier fourni) :** `2026-09-22 - Docker.md`, daté du 22/09/2026 ; auteur du module indiqué : Gavin Chaineux. Le fichier cite un original « Docker v2-5.pdf » et des projets `docker` / `rag`. L'original n'a pas été ouvert ici.

**Dépôt personnel, références vérifiées sur `main` :**

- Ollama + Open WebUI : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/formation/docker-httpd/docker-compose.yaml
- n8n + PostgreSQL (sauvegarde de config historique, pas garantie active) : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/docker-compose.yml.save
- Script B5 PostgreSQL/Qdrant : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/setup.sh
- Instructions Z4 et endpoints vLLM : https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md
- Workflow B5 (deux exports n8n) : https://github.com/Mircea11/BF_IntegIA_2026/tree/main/N8N/B5_conseiller_produit_v2

**Vérification technique externe (documentation officielle Docker, consultée le 26/10/2026) :**

- Réseaux Compose : https://docs.docker.com/compose/how-tos/networking/
- Démarrage et healthcheck : https://docs.docker.com/compose/how-tos/startup-order/
- Persistance des volumes : https://docs.docker.com/engine/storage/volumes/
- Validation sans affichage : https://docs.docker.com/reference/cli/docker/compose/config/
- Variables d'environnement et secrets : https://docs.docker.com/compose/how-tos/environment-variables/best-practices/

**À conserver pour la suite :** une page de schéma technique de ton Z4, avec les noms réellement observés, et un tableau des sauvegardes *réalisées* versus seulement *prévues*. Le prochain support de la collection est le cours 14, **RAG, extraction et chunking avec Docling**.
