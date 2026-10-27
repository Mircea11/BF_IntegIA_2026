# Cours personnel 12 — Servir un LLM en local : llama.cpp et vLLM

**Formation AI Integration Specialist · Consolidation personnelle · 26 octobre 2026**  
**Support de départ :** `2026-09-18_10-01 - Servir un LLM (llama.cpp et vLLM).md` dans `2026 Cours.zip`, synthèse du collègue, période 18 septembre–1er octobre 2026.  
**Sources du professeur :** ressources du module de Romain Wauman, conservées dans `formation/vLLM/full_llama_vllm/` sur GitHub, particulièrement `00_build_and_serve.md`, `04_gguf.md`, `05_vllm_vs_llama_server.md` et `exos/02_chat_boucle.ipynb`.  
**Sources personnelles :** notes de travail et échanges des 14–23 octobre 2026 ; dépôt `Mircea11/BF_IntegIA_2026`, notamment B5, RAG et le rapport d'exécution de Nemotron.  
**Durée suggérée :** 80–110 minutes de lecture, puis trois blocs pratiques de 45 minutes.  
**Prérequis :** Python et API (cours 02 et 07), Docker/Linux (bases), embeddings/RAG et tokens (cours 09).  
**Objectif :** comprendre ce que font les moteurs d'inférence, retrouver la provenance des réglages de ton Z4, vérifier un service sans perturber les autres et pouvoir diagnostiquer seul une panne élémentaire.

> **Trois niveaux de preuve.** « Présent dans les notes du professeur » signifie que le sujet a été enseigné. « Présent dans ton code ou tes journaux » signifie que tu l'as rencontré ou utilisé, parfois avec assistance. « Maîtrisé seul » reste à démontrer par les exercices. Le document n'affirme pas que tu as personnellement compilé llama.cpp ou benchmarké plusieurs modèles.

## 1. Pourquoi ce cours est central pour ton parcours

Ton projet B5 répond à une question métier (« Quel produit puis-je recommander ? »), mais le LLM n'est qu'une composante d'une chaîne :

```text
Client / formulaire n8n
         |
         v
 Python / orchestration / règles métier
         |
         +--> API de Nemotron (vLLM, port 8000) : classifier, reformuler, générer
         |
         +--> API de BGE-M3 (vLLM, port 8001) : convertir texte en vecteur
         |                                        |
         |                                      Qdrant : recherche vectorielle
         |
         +--> Catalogue DummyJSON : prix et stock en direct
         |
         +--> PostgreSQL : mémoire persistante par session
         |
         v
 Réponse vérifiée par des règles déterministes
```

**Question de contrôle :** si Nemotron produit un nom de produit absent du catalogue, qui doit corriger ? **Le code métier**, pas une consigne vague au modèle. Dans B5, les contrôles de stock, d'identité du produit et de budget sont explicites dans `app.py`. Le moteur d'inférence sert du texte : il ne détient aucune vérité sur les stocks.

Dans les travaux RAG, BGE-M3 transforme le texte en vecteur ; il **ne rédige pas** une réponse. Nemotron génère la réponse ; il **n'effectue pas** une recherche documentaire sans qu'une application ne lui fournisse les données pertinentes.

## 2. Ce que les trois sources apportent réellement

| Provenance | Éléments exploités | Limite à garder en tête |
|---|---|---|
| **Professeur, `00_build_and_serve.md`** | Pilote NVIDIA versus CUDA Toolkit, compilation facultative de llama.cpp, `llama-server`, `-c`, `-np`, `-ub`, `-ngl`, adresse d'écoute | C'est un exemple de démonstration, pas une commande à relancer telle quelle sur le Z4 |
| **Professeur, `04_gguf.md`** | Structure GGUF, métadonnées, quantification, estimation du KV cache | Les tailles théoriques doivent être comparées aux logs ; architecture hybride = formule imparfaite |
| **Professeur, `05_vllm_vs_llama_server.md`** | Comparaison des moteurs, PagedAttention, démarrage, cache, débit, sécurité, métriques | Version du cours : vLLM 0.30 (septembre 2026) ; options susceptibles de changer |
| **Exercice du professeur `02_chat_boucle.ipynb`** | Streaming, historique de conversation, alerte de contexte, `/reset` | Il s'agit d'un énoncé avec des `TODO`, pas de la preuve d'un exercice terminé |
| **Synthèse du collègue** | Notes datées, mesures de cours, TP, erreurs relevées dans `exo4.ipynb`, compléments de cours | C'est une synthèse secondaire ; les erreurs attribuées à `exo4` n'ont pas toutes été vérifiées sur un original local |
| **Tes traces B5 et RAG** | API sur 8000/8001, serveur `veltis-llm`, modèle `bge-m3`, vecteurs de 1 024 dimensions, tests et appels réels | Certaines sorties peuvent venir d'une assistance ; niveau autonome non présumé |

### Le chemin de lecture recommandé

1. Lis ce document pour construire la carte d'ensemble.
2. Ouvre le **support du professeur** sur les options que tu as réellement utilisées.
3. Compare avec les commandes de démarrage présentes dans le `README_SETUP_FR.md` du B5 ; ne les exécute pas avant les diagnostics.
4. Fais les exercices en **lecture seule**. N'installe pas un second vLLM ou llama-server sur la même carte pour « tester ».

## 3. Modèle, poids, moteur, serveur et client : cinq objets différents

**Modèle** : architecture mathématique et paramètres d'apprentissage (ex. Nemotron ou BGE-M3).  
**Poids** : les nombres appris, stockés en fichiers (`safetensors`, GGUF...).  
**Moteur d'inférence** : programme qui utilise ces poids pour effectuer le calcul (`vLLM`, `llama.cpp`, Ollama...).  
**Serveur** : expose ce moteur sur un port HTTP ; la commande `vllm serve` en lance un.  
**Client** : n8n, Python, `curl`, l'interface utilisateur ou le SDK OpenAI qui lui envoie des requêtes.

Un *modèle de génération* prédit des tokens de sortie. Un *modèle d'embedding* renvoie un vecteur numérique ; le même type d'API compatible OpenAI ne signifie pas que les modèles ont les mêmes tâches.

| Cas | Type de réponse | Endpoint exemplaire |
|---|---|---|
| Nemotron `veltis-llm` | Texte produit | `POST /v1/chat/completions` |
| BGE-M3 `bge-m3` | Liste de nombres (vecteur) | `POST /v1/embeddings` |
| Serveur : inventaire | Liste des modèles servis | `GET /v1/models` |
| Service vivant ? | Diagnostic superficiel | `GET /v1/models` ne garantit PAS qu'une inférence marchera |

L'API compatible OpenAI est un **protocole d'échange** ; elle n'implique ni utilisation du cloud OpenAI, ni transfert de tes données à OpenAI. Ton environnement B5 vise des serveurs locaux.

## 4. llama.cpp versus vLLM : ce qui change

| Critère | `llama-server` (llama.cpp) | `vLLM` |
|---|---|---|
| Fichiers usuels | GGUF | Répertoire Hugging Face / safetensors ; quantisations compatibles |
| Calcul | CPU, GPU ou combinaison, selon modèle et build | Fortement orienté GPU ; modes matériels supplémentaires selon version |
| GPU insuffisant | Couches et parfois experts déportés en RAM | Offload possible selon version, mais coût élevé ; contraintes de mémoire plus fortes |
| Optimisation | Contexte, offload, micro-batches, quantisations fines | Continuous batching, gestion paginée du KV cache, forte concurrence |
| Déploiement individuel | Souvent simple et souple | Pertinent aussi localement ; meilleur intérêt quand plusieurs requêtes coexistent |
| API | Compatible OpenAI | Compatible OpenAI |
| **Dans ton Z4** | Appris au cours ; exécution personnelle non prouvée ici | **Utilisé** pour Nemotron et BGE-M3 |

**Nuance documentaire :** certains supports opposent « llama.cpp = un utilisateur » et « vLLM = beaucoup d'utilisateurs ». Ce sont les *usages typiques*, pas une impossibilité technique : les deux disposent aujourd'hui de fonctions de parallélisme et de batching. Le choix dépend du modèle, du matériel, de la mémoire, de l'environnement et du type de charge.

### Exemple du professeur — à comprendre, pas à exécuter sans préparation

```bash
# Exemple didactique issu de 00_build_and_serve.md
llama-server \
  -m /chemin/vers/le/modele.gguf \
  -c 65536 \
  -np 1 \
  -fa on \
  -b 2048 -ub 512 \
  -ngl 99 \
  --host 127.0.0.1 --port 8080
```

`-m` choisit les poids ; `-c` le contexte total ; `-np` les slots ; `-fa` Flash Attention ; `-b` et `-ub` le batch logique et le micro-batch ; `-ngl` les couches placées sur le GPU. **Ni le chemin de démonstration ni les 65 536 tokens ne correspondent nécessairement au Z4 actuellement disponible.**

## 5. Formats et quantification : GGUF, safetensors, BF16, Q4

**GGUF** n'est pas synonyme de « quantifié ». C'est un conteneur comprenant notamment les poids et des métadonnées : architecture, tokenizer, contexte, modèle de conversation. Il existe des GGUF F16.  
**safetensors** est un format de stockage fréquent dans les modèles Hugging Face. Des poids safetensors peuvent eux aussi être quantifiés : AWQ, GPTQ, FP8, etc.  
**Quantification** signifie représenter des poids et/ou des caches avec moins de bits, ce qui réduit généralement la mémoire au prix d'éventuelles pertes de précision.

Le cours du professeur explique qu'un fichier **Q4_K_M** mélange souvent plusieurs types de tenseurs : le nom représente une recette de quantification, non une conversion uniforme de tous les poids.

**À retenir pour ton matériel :** un modèle de « 8 milliards de paramètres » ne tient pas dans 8 Go en BF16. Ordre de grandeur des *poids seuls* : 8 milliards × 2 octets ≈ 16 Go décimaux, auxquels s'ajoutent KV cache, activations et buffers. Un nom de modèle ou un nombre de paramètres ne suffit pas à prévoir l'occupation réelle de VRAM.

## 6. Contexte, KV cache et mémoire GPU

Un moteur de génération traite deux grandes phases :

**Prefill** — lire et encoder le prompt d'entrée, souvent en parallèle.  
**Decode** — produire les tokens de réponse, en réutilisant les clés et valeurs des tokens précédents dans le **KV cache**.

Le KV cache est de la mémoire consacrée à l'attention pendant la génération. Dans le cas simple d'une attention homogène, l'ordre de grandeur est :

```text
mémoire KV ≈ 2 × couches × têtes_KV × dimension_par_tête × tokens × octets_par_valeur
             ↑ clés + valeurs
```

Le modèle du professeur rappelle que les architectures à attention locale, glissante ou hybride ne respectent pas toujours cette formule simple.

**Piège fréquent :** `--max-model-len 2048` limite la longueur acceptée par requête. Ce n'est **pas** un paramètre indiquant directement « réserver exactement 2048 tokens × telle taille » dans tous les moteurs. Avec vLLM, le cache résulte de la mémoire allouée après le chargement des poids et des autres buffers.

### Ton cas : les mesures relevées sur le Z4

Dans tes notes d'octobre :

- **GPU** : NVIDIA RTX PRO 4000 Blackwell, environ **24 467 MiB** de VRAM totale indiqués dans un relevé du 20 octobre.
- **Nemotron** : service vLLM sur **8000** avec nom servi `veltis-llm`, contexte réglé à **2048** pour des tests locaux ; `--gpu-memory-utilization 0.50`, `--max-num-seqs 1`, `--enforce-eager` ont été utilisés dans des commandes de travail.
- **BGE-M3** : service vLLM sur **8001**, mode **`--runner pooling`**, servant des embeddings de **1 024 dimensions**.
- **n8n** : lancé dans Docker ; accès aux services hôtes via l'adresse de passerelle **`172.21.0.1`** dans tes workflows.

**Attention :** `--gpu-memory-utilization` est un budget par instance, pas une mesure instantanée « 50 % du GPU est occupé ». Le total sur la machine doit tenir compte des deux serveurs et de tous les autres processus GPU. Le relevé du 20 octobre (Nemotron ~15 716 MiB, ~8 270 MiB libres) est un instantané ancien, **pas l'état actuel du GPU**.

## 7. Lire la commande vLLM du Z4

La documentation B5 comporte une commande de référence pour Nemotron :

```bash
# Référence documentaire : vérifier le serveur déjà actif AVANT tout lancement
vllm serve /home/bm/models/nemotron3-nano-4b/vllm \
  --served-model-name veltis-llm \
  --host 172.21.0.1 --port 8000 \
  --gpu-memory-utilization 0.50 \
  --max-model-len 2048 \
  --max-num-seqs 1 \
  --enforce-eager
```

Et pour BGE-M3 :

```bash
vllm serve /home/bm/models/rag/embedder/bge-m3 \
  --runner pooling --served-model-name bge-m3 \
  --host 172.21.0.1 --port 8001 \
  --gpu-memory-utilization 0.20 --max-model-len 1024
```

Ces lignes sont **des références historiques issues des fichiers**, **pas des commandes à lancer maintenant**. Elles doivent être confrontées aux processus actifs et à la version de vLLM réellement installée. Ne lance jamais une seconde instance de Nemotron/BGE-M3 pour vérifier la première.

| Flag | Ce qu'il règle | Question à savoir expliquer |
|---|---|---|
| `--served-model-name` | Identifiant visible dans `/v1/models` | Pourquoi le client demande-t-il `veltis-llm` plutôt que le chemin du dossier ? |
| `--host` | Interface réseau d'écoute | Pourquoi un serveur visible depuis Ubuntu peut-il être invisible depuis Docker ? |
| `--port` | Numéro du service HTTP | Pourquoi Nemotron et BGE-M3 doivent-ils être sur des ports distincts ? |
| `--runner pooling` | Exécution de type embeddings/pooling | Pourquoi cette option ne convient-elle pas au modèle génératif ? |
| `--gpu-memory-utilization` | Part de VRAM allouable à une instance | Que se passe-t-il si la somme demandée dépasse le disponible ? |
| `--max-model-len` | Plafond de contexte accepté | Que devient une requête trop longue ? |
| `--max-num-seqs` | Plafond de séquences simultanées | Pourquoi choisir 1 durant les premiers diagnostics ? |
| `--enforce-eager` | Évite certaines optimisations de compilation/capture | Pourquoi tester d'abord simplement, puis benchmarker ? |

## 8. L'API OpenAI-compatible : réussir une vraie requête

### 8.1. Vérifications **en lecture seule**

Depuis Ubuntu, sans démarrer ni arrêter de service :

```bash
nvidia-smi
ss -ltn | grep -E ':(8000|8001|6333|5678)\b' || true
curl -fsS --max-time 5 http://172.21.0.1:8000/v1/models
curl -fsS --max-time 5 http://172.21.0.1:8001/v1/models
```

Si l'une des adresses ne répond pas, **ne devine pas** l'adresse et **ne redémarre pas** les moteurs ; regarde quel processus écoute, quel port et quelle interface. `127.0.0.1` fonctionne pour les services attachés au loopback, mais une connexion depuis Docker doit atteindre une adresse accessible sur le réseau du conteneur.

### 8.2. Requête de génération minimale

```bash
curl -fsS --max-time 30 http://172.21.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"veltis-llm",
    "messages":[{"role":"user","content":"Explique en une phrase le KV cache."}],
    "temperature":0,
    "max_tokens":60
  }' | python3 -m json.tool
```

Contrôle trois champs : `choices[0].message.content`, `usage.prompt_tokens` et `usage.completion_tokens`. Si une erreur apparaît, relève **le statut HTTP et le texte**, puis stoppe le test ; n'augmente pas la VRAM au hasard.

### 8.3. Requête embeddings minimale

```bash
curl -fsS --max-time 30 http://172.21.0.1:8001/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"bge-m3","input":"production et prévisions"}' \
  | python3 -c 'import json,sys; o=json.load(sys.stdin); print("dimension:",len(o["data"][0]["embedding"]))'
```

**Résultat attendu dans ton environnement :** `dimension: 1024`. Cela vérifie l'inférence, contrairement à `/v1/models` qui vérifie seulement la présence de l'endpoint. Le notebook RAG contient des exemples BGE-M3 dont la sortie imprimée a une forme `(1024,)`.

### 8.4. Une liste de messages n'est pas une mémoire autonome

Une requête de chat utilise `system`, `user`, `assistant`. Le serveur d'inférence traite ce qui lui est transmis : il n'entretient **pas, à lui seul, une mémoire conversationnelle permanente**. Dans B5, PostgreSQL stocke l'historique et le profil ; la couche applicative recompose les informations nécessaires à chaque nouveau tour.

Le professeur propose un mini-chat en streaming avec `/reset`, `/history` et contrôle de la fenêtre de contexte. **Attention :** cet exercice `02_chat_boucle.ipynb` contient des cases `TODO`. Sa présence sur GitHub ne prouve pas sa réalisation complète.

## 9. Latence et performance : mesurer sans confondre

| Terme | Ce que tu mesures |
|---|---|
| **TTFT** (*time to first token*) | Délai jusqu'au premier token, comprenant selon le contexte file d'attente et prefill |
| **TPOT** | Temps moyen de génération par token |
| **ITL** | Intervalle entre tokens successifs |
| **tok/s** | Débit des tokens ; il faut préciser si c'est par utilisateur ou global |
| **Throughput** | Débit total des demandes ou des tokens à concurrence donnée |
| **P95/P99** | Seuils de latence des requêtes les plus lentes |

### Exemple réel du rapport n8n A1/Nemotron

Le rapport `N8N/data/rapport_usage_modele.json` décrit une exécution du **19 octobre 2026** :

| Mesure | Valeur enregistrée |
|---|---:|
| Prompt | 446 tokens |
| Réponse | 106 tokens |
| Total | 552 tokens |
| Durée de bout en bout du workflow | 5,393 secondes |
| Ratio calculé de sortie | ≈ 19,66 tokens/s **de bout en bout** |
| Température | 0,2 |
| Limite de contexte enregistrée | 2 048 tokens |
| Part du contexte consommée selon ce rapport | 0,2178 |

**Le ratio ≈ 19,66 tok/s n'est PAS la vitesse native du moteur** : le chronométrage comprend l'orchestration n8n. Pour une mesure comparable à celle du professeur, il faut mesurer séparément les appels réseau, les premiers tokens, le prefill et le decode ; répéter le test avec des entrées de taille similaire.

Le support du collègue rapporte aussi des mesures sur **Qwen3.8-27B Q4** et une carte de 24 Go, notamment des gains avec des optimisations du KV cache et du speculative decoding. Ce sont **des résultats du cours**, pas tes benchmarks Nemotron : ne mélange pas ces deux séries de chiffres.

### Pourquoi ne pas « optimiser » tout de suite

Le bon protocole est : **1)** capturer l'état actuel, **2)** formuler une hypothèse, **3)** ne changer qu'un paramètre, **4)** mesurer à entrée et charge comparables, **5)** conserver les résultats. Avec deux modèles servis sur le même GPU, augmenter l'allocation mémoire de Nemotron peut empêcher BGE-M3 de démarrer.

## 10. Déboguer sans toucher à la configuration

| Symptôme | Test minimal | Diagnostic possible | Ce qu'il ne faut pas conclure |
|---|---|---|---|
| `/v1/models` répond, `/v1/embeddings` renvoie `501` | Envoyer un texte court au bon endpoint | Runner / opération non supportée pour cette instance | « BGE-M3 calcule correctement des embeddings » |
| Appel fonctionne depuis Ubuntu mais timeout dans n8n | Comparer hôte et conteneur ; adresse écoutée | Liaison entre Docker et hôte, firewall ou bind incorrect | « GPU insuffisant » |
| Service démarre et GPU semble plein | Lire logs + `nvidia-smi` | Allocation vLLM volontaire, KV cache, autres processus | « fuite mémoire » sans observation supplémentaire |
| Réponse incohérente ou hors catalogue | Examiner prompt, récupération, contrôle métier | Mauvais contexte ou règle absente | « changer de modèle suffit » |
| Erreur HTTP 400, prompt trop long | Mesurer tokens et `--max-model-len` | Dépassement de fenêtre | « augmenter `max_tokens` » |
| Timeout API / LLM | Vérifier disponibilité et taille de requête | Inférence lente, saturation, souci réseau | « relancer le même processus deux fois » |

**Épisodes documentés dans nos échanges :** (a) le 20 octobre, BGE-M3 avait un endpoint de modèle visible mais une requête embeddings a d'abord renvoyé HTTP 501 ; (b) le 22 octobre, le port 8001 répondait depuis Ubuntu mais pas depuis le conteneur n8n. Ces difficultés ont servi à apprendre qu'un système opérationnel dépend du **modèle + endpoint + réseau + application**, et pas du seul téléchargement des poids. Leur résolution sur l'état actuel du Z4 doit être vérifiée par les exercices : ne présume pas qu'un ancien correctif reste valable.

## 11. Sécurité et limites d'un prototype local

1. Ne pas exposer `--host 0.0.0.0` ni le port 8765 sur Internet sans contrôle d'accès, segmentation et journalisation adaptés.
2. Vérifier les conséquences réseau de la passerelle Docker `172.21.0.1` : elle n'est pas équivalente à une protection d'accès.
3. Éviter de copier mots de passe, tokens ou fichiers `.env` dans GitHub public.
4. Ne pas utiliser des documents internes de formation ou des données personnelles comme corpus public sans droit de diffusion.
5. Les API non protégées par `--api-key` dépendent de la version vLLM : la documentation officielle avertit que **l'authentification n8n/API ne garantit pas la protection de tous les endpoints**. Pour un prototype sur le Z4, garder l'interface non exposée publiquement.

## 12. Trois blocs pratiques de 45 minutes (sans modification des services)

### Bloc A — Cartographie de ton serveur (45 min, lecture seule)

**Sans ChatGPT et sans relancer vLLM :**

1. Fais un schéma avec six boîtes : n8n, Nemotron, BGE-M3, Qdrant, PostgreSQL, catalogue.
2. Associe chaque boîte à son rôle (générer, vectoriser, retrouver, mémoriser, valider, orchestrer).
3. Relève les ports et l'adresse du point de vue de **l'hôte** et de **Docker**.
4. Exécute seulement `nvidia-smi`, `ss -ltn` et les deux requêtes `/v1/models`.
5. Note « observé / non vérifié » pour chaque service.

**Livrable :** `etat_llm_z4.md` en local, daté, avec cinq lignes observées et aucune donnée secrète.

### Bloc B — Contrôler une réponse et un embedding (45 min)

1. Depuis un terminal, envoie **une** demande de texte court à Nemotron et relève les tokens (sans changer le modèle).
2. Envoie **une** phrase courte à BGE-M3 et relève la dimension du vecteur.
3. Explique à voix haute pourquoi les deux sorties ne sont pas comparables.
4. Calcule `106 / 5.393` ; explique pourquoi ce résultat n'est pas le débit GPU pur.
5. Relève le premier message d'erreur complet **si un test échoue**, sans réinstaller.

**Livrable :** tableau « requête → endpoint → réponse → contrôle → conclusion ».

### Bloc C — Comparaison théorique et diagnostic (45 min)

1. Pour les huit flags de la section 7, rédige une définition en **une phrase** sans consulter cette page.
2. Explique à une autre personne « modèle, moteur, serveur, client » en 90 secondes.
3. Décris comment tu vérifierais le symptôme « Ubuntu OK / n8n timeout », **sans exécuter de modifications**.
4. Reprends `02_chat_boucle.ipynb` : identifie les `TODO` et rédige un pseudocode de l'historique, de `/reset` et du seuil de 80 %.
5. Justifie en cinq phrases ton choix actuel de vLLM pour B5, et un cas où tu envisagerais llama.cpp.

**Livrable :** réponses autonomes courtes. Ne te note « je sais faire seul » que si tu peux expliquer et reproduire les étapes sans copier les commandes.

## 13. Autotest — 12 questions et réponses attendues

1. **Différence entre modèle et moteur ?** Poids/architecture appris vs logiciel qui exécute l'inférence.
2. **Nemotron ou BGE-M3 : lequel génère des phrases ?** Nemotron ; BGE-M3 renvoie des vecteurs.
3. **Pourquoi GGUF n'implique pas obligatoirement quantification ?** GGUF est un format conteneur ; il peut contenir du F16.
4. **Que fait le KV cache ?** Conserve K/V des tokens pour éviter de recalculer l'attention historique à chaque nouveau token.
5. **Différence prefill/decode ?** Traitement du prompt versus génération séquentielle de nouveaux tokens.
6. **`--served-model-name` ?** Identifiant du modèle exposé au client dans l'API.
7. **`--max-model-len` et VRAM ?** Plafond par requête ; la mémoire résulte aussi du poids du modèle, du cache et des autres allocations.
8. **Pourquoi `nvidia-smi` seul ne mesure pas la vitesse ?** Il montre l'utilisation de ressources, pas TTFT ni tok/s.
9. **Pourquoi `/v1/models` ne valide pas BGE-M3 ?** Parce qu'il ne prouve pas que `/v1/embeddings` fonctionne.
10. **Pourquoi un chat local perd-il son prénom au redémarrage sans stockage ?** Le serveur de modèles ne stocke pas durablement l'historique ; mémoire applicative et PostgreSQL nécessaires.
11. **Pourquoi le port 8001 peut-il marcher sur Ubuntu et échouer dans Docker ?** Réseau, interface d'écoute, route et pare-feu peuvent différer.
12. **En cas de push d'un mauvais prix, qui protège l'utilisateur ?** La validation métier en code sur les données catalogue contrôlées, pas une génération libre du modèle.

**Barème personnel :** 0 = entendu seulement ; 1 = identifié dans ton code ; 2 = expliqué correctement sans notes ; 3 = reproduit sur le Z4 sans aide et avec sortie enregistrée. Ces niveaux ne sont **pas** des certifications.

## 14. Après ce cours : la suite sans dispersion

Ce module termine la compréhension du **service du modèle**. Le cours suivant approfondira **Docker** : volumes, réseau, conteneurs, gestion des dépendances, persistence PostgreSQL/Qdrant et risques de redémarrage. Puis les cours **RAG/Docling et ETL** permettront de comprendre le trajet complet du document à la réponse sourcée.

Pour ton portfolio d'intégration IA, le prochain artefact utile n'est **pas** un nouveau modèle entraîné ni un moteur supplémentaire. C'est une **fiche d'architecture et de tests reproductibles** montrant que B5 sait vectoriser, rechercher, refuser un produit indisponible, conserver l'historique et signaler proprement une panne.

## Références vérifiées et lecture complémentaire

**Support du collègue**  
- `2026 Cours.zip` → `2026-09-18_10-01 - Servir un LLM (llama.cpp et vLLM).md` (notes de Romain Wauman reconstruites, 18 septembre–1er octobre).

**Supports du professeur présents dans ton dépôt GitHub**  
- [Construction et lancement de llama.cpp](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/formation/vLLM/full_llama_vllm/demo/00_build_and_serve.md)  
- [Lire les métadonnées GGUF](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/formation/vLLM/full_llama_vllm/demo/04_gguf.md)  
- [vLLM et llama-server : correspondances](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/formation/vLLM/full_llama_vllm/demo/05_vllm_vs_llama_server.md)  
- [Exercice de mini-chat et historique](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/formation/vLLM/exos/02_chat_boucle.ipynb)  
- [Dossier vLLM et supports associés](https://github.com/Mircea11/BF_IntegIA_2026/tree/main/formation/vLLM/full_llama_vllm)

**Tes fichiers de travail et résultats**  
- [B5 : configuration documentée du Z4](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/README_SETUP_FR.md)  
- [B5 : code métier Python et appels API](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py)  
- [B5 : scénarios de test](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/test_b5.py)  
- [RAG : notebook BGE-M3 et embeddings](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/RAG/rag-20261014T092905Z-1-003/rag/demo_live/demo_chunking_embedding.ipynb)  
- [Nemotron : rapport réel des tokens et de la latence](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/data/rapport_usage_modele.json)

**Documentation technique, à vérifier selon la version locale**  
- [vLLM — serveur compatible OpenAI](https://docs.vllm.ai/en/stable/serving/online_serving/openai_compatible_server/)  
- [vLLM — options CLI](https://docs.vllm.ai/en/latest/cli/)  
- [llama.cpp — documentation du serveur](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

> **Traçabilité.** Les paramètres de démonstration Qwen3 proviennent du support du professeur / du résumé du collègue. Les ports 8000/8001 et `veltis-llm`/`bge-m3` proviennent des fichiers de ton projet B5 ; les chiffres du 19 octobre viennent du JSON de rapport. Les notes historiques d'octobre sur la VRAM et les problèmes réseau viennent de nos échanges et ne remplacent pas un diagnostic actuel.
