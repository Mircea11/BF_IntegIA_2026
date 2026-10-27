# Cours personnel 10 — Git, GitHub et sauvegarde du travail

**Formation AI Integration Specialist · Consolidation personnelle · 26 octobre 2026**  
**Support principal :** `2026-09-04_08 - Git.md` (module Davit Nersesyan, 4 et 8 septembre 2026) dans `2026 Cours.zip`.  
**Étude de cas personnelle :** dépôt `Mircea11/BF_IntegIA_2026`, branche `main`, commits et fichiers contrôlés sur GitHub le 26 octobre 2026 ; commandes et erreurs reproduites à partir de nos échanges.  
**Durée :** 65–85 min de lecture + trois blocs de pratique de 45 min, à espacer si nécessaire.  
**Prérequis :** savoir naviguer dans un terminal et distinguer un fichier source d'un fichier généré.  
**Objectif professionnel :** versionner un travail technique, expliquer son historique, collaborer sans perdre de données et publier une preuve de travail vérifiable.

> **Statut des preuves.** Le support décrit le dépôt d'exercice `git` du cours (branches `dev`, `test`, `test2`, conflits, stash, revert, trois pull requests) ; ce dépôt d'exercice n'a pas été vérifié ici. En revanche, ton dépôt de formation et les commits cités ci-dessous ont été contrôlés directement. Les commandes que tu as exécutées avec aide sont des opérations réussies, mais elles ne prouvent pas encore une autonomie sans assistance.

## 1. Carte mentale : Git n'est pas GitHub

**Git** est l'outil local qui gère les versions d'un ensemble de fichiers. Il enregistre les changements dans des **commits**. **GitHub** héberge une copie distante du dépôt et permet la collaboration (pull requests, issues, revue du code). Ton PC peut contenir un commit que GitHub ne connaît pas encore ; inversement, GitHub peut recevoir un commit depuis une autre machine ou une interface web.

```text
Ton PC : ~/formation

Répertoire de travail       Index / staging         Historique LOCAL       GitHub / origin/main
(fichiers modifiés)  --add-->  (sélection)   --commit--> (commits)    --push--> (commits distants)
       ^                                                                         |
       +------------------- fetch puis merge / rebase (pull) -------------------+
```

Un **commit** est un instantané du projet (pas seulement une liste de fichiers) repéré par un SHA. Une **branche** est un pointeur mobile vers un commit. `HEAD` indique ta position actuelle ; habituellement, il référence la branche sur laquelle tu travailles.

| Terme vu dans ton terminal | Sens | Action typique |
|---|---|---|
| `??` / *untracked* | Fichier présent sur disque, non suivi | `git add chemin` si tu veux publier |
| `M` / *modified* | Fichier suivi, modifié depuis la version Git | Contrôler avec `git diff` |
| `D` / *deleted* | Fichier suivi mais absent localement | Ne pas indexer la suppression si elle doit rester locale |
| *staged* / indexé | Version choisie pour le prochain commit | Vérifier avec `git diff --cached` |
| *committed* | Version enregistrée localement | Publier avec `git push` |
| `origin/main` | Dernier état connu localement de la branche distante | Mettre à jour avec `git fetch origin` |

**Exemple réel :** tu avais des fichiers RAG `D`, des résultats générés non suivis `??` et 18 fichiers sélectionnés (`A` et `M`). Tu as décidé de pousser les 18 fichiers sans supprimer les fichiers RAG du dépôt distant. L'index t'a permis de faire cette sélection.

## 2. Lire avant d'agir : cinq commandes sûres

Ouvre ton dépôt réel, **sans modifier de fichier** :

```bash
cd ~/formation
pwd
git status -sb
git log -5 --oneline --graph --decorate
git remote -v
git diff --stat
```

- `git status -sb` : branche, suivi distant, modifications locales. `## main...origin/main` indique que les références locales ont le même nombre de commits ; il ne vérifie pas seul que le serveur est accessible à cet instant.
- `git log` : historique des instantanés. `--all` ajoute les autres branches connues ; `--graph` affiche leur structure.
- `git remote -v` : URL utilisée pour lire (*fetch*) et écrire (*push*), SSH ou HTTPS.
- `git diff` : modifications **non indexées**. `git diff --cached` : modifications qui entreraient dans le prochain commit.
- `git show --stat SHA` : résumé des fichiers touchés par un commit ; `git show SHA -- chemin` examine un fichier précis.

**Référence directe :** [historique du dépôt](https://github.com/Mircea11/BF_IntegIA_2026/commits/main) ; [commit B5 du 26 octobre 2026](https://github.com/Mircea11/BF_IntegIA_2026/commit/c17017e8a2ae4f7872ed092747d785d42a6be915).

## 3. `add` → `commit` → `push` : trois opérations différentes

**`git add`** construit la sélection. **`git commit`** l'enregistre sur le PC. **`git push`** transfère les commits vers GitHub, à condition de pouvoir s'authentifier et de ne pas écraser des changements distants.

```bash
# Exemple pédagogique (à lancer dans le laboratoire du § 10, PAS sur main pour apprendre)
git status
git add programme.py
git diff --cached --name-status
git diff --cached --check
git commit -m "Add product availability check"
git log -1 --oneline
```

Ton cas réel :

```text
[main ba0f8ed] Add B5 AI product advisor and RAG training exercises
18 files changed, 3341 insertions(+), 28 deletions(-)
```

**Ce message prouvait uniquement le commit local.** Tant que la commande `git push` échouait, GitHub ne disposait pas de cette mise à jour. Les 18 fichiers étaient dans l'historique local, pas encore dans `origin/main`.

### Sélectionner sans supprimer

Au cours de la sauvegarde, tu souhaitais conserver huit suppressions locales hors du commit. La commande utilisée était :

```bash
git add --ignore-removal .
git diff --cached --name-status
```

`--ignore-removal` ignore les fichiers suivis supprimés dans le répertoire de travail, mais **il faut vérifier l'index après coup** : `A` signifie ajouté, `M` modifié, `D` supprimé. Évite `git add -A` si tu ne veux pas intégrer des suppressions. `git restore --staged fichier` retire un fichier de l'index sans effacer sa modification locale.

**Précaution :** `git commit -a` sélectionne les fichiers déjà suivis, y compris leurs suppressions, et n'inclut pas les nouveaux fichiers. Il ne correspondait donc pas à ton besoin du 26 octobre.

## 4. Étude de cas vérifiée : pourquoi ton `push` a échoué

L'incident d'octobre est une excellente leçon de Git : **une erreur réseau et une erreur d'historique sont deux problèmes différents**.

| Étape | Ce qui s'est réellement produit | Ce que tu devais vérifier |
|---|---|---|
| Commit local | `ba0f8ed` a été créé sur ton PC | `git log -1 --oneline` |
| Premier blocage | `git push` restait sans réponse | Connexion et identité SSH, pas refaire le commit |
| Diagnostic | GitHub acceptait une clé mais l'agent local restait bloqué pendant la signature | `ssh -vvv`, ligne `Server accepts key`, puis opération de signature |
| Résolution SSH | Tu as utilisé `~/.ssh/github_formation`, port 443, en contournant l'agent | `ssh -T -p 443 -o IdentityAgent=none ...` |
| Deuxième erreur | `main -> main (fetch first)` | Le distant possédait un commit absent de ton PC |
| Sauvegarde temporaire | `git stash push -u` a écarté les modifications non committées | `git status` puis `git stash list` |
| Réconciliation | `git pull --rebase origin main` a réussi | Le commit local a été rejoué après le commit distant |
| Publication | `8ce79ce..c17017e  main -> main` | GitHub confirme la mise à jour de la branche |
| Restauration | `git stash pop` a rétabli les fichiers exclus | `git status` montre `D`, `M` et `??` comme avant |

Le commit distant **`8ce79ce`**, ajouté directement sur GitHub, contenait un checkpoint B5. Ton commit local **`ba0f8ed`** avait été créé avant d'intégrer ce checkpoint. Le rebase a replacé tes changements sur l'historique GitHub ; **le même travail a reçu un nouveau SHA, `c17017e`**. Ce dernier est bien présent sur `main`.

**Preuves :** [checkpoint `8ce79ce`](https://github.com/Mircea11/BF_IntegIA_2026/commit/8ce79ce44b671b26f9dd1bd3832cda42567e45e9) ; [commit final `c17017e`](https://github.com/Mircea11/BF_IntegIA_2026/commit/c17017e8a2ae4f7872ed092747d785d42a6be915). Le détail des étapes SSH/stash provient de tes sorties de terminal partagées dans nos échanges.

**À retenir :** « commit créé » ≠ « sauvegardé sur GitHub » ; « authentification réussie » ≠ « historique compatible » ; « dépôt synchronisé » ≠ « tous les fichiers locaux sont publiés ».

## 5. `fetch`, `pull`, `merge` et `rebase`

`git fetch origin` **télécharge** les informations distantes sans modifier tes fichiers de travail. Tu peux inspecter les divergences avant d'intégrer :

```bash
git fetch origin
git log --oneline --left-right HEAD...origin/main
git diff --stat HEAD..origin/main
```

`git pull` combine *fetch* et intégration. Selon les options et la configuration Git, il utilise un **merge** ou un **rebase** ; ne suppose pas qu'il fait toujours la même chose.

| Méthode | Résultat | Pour ton usage |
|---|---|---|
| `git merge origin/main` | Fusion des historiques, avec commit de merge si nécessaire | Préserve les SHA existants |
| `git rebase origin/main` | Rejoue tes commits locaux après le distant | Historique linéaire, **nouveaux SHA** |
| `git pull --rebase origin main` | Fetch puis rebase de tes commits locaux | C'est la commande qui a résolu ton incident |
| `git push --force` | Remplace potentiellement le travail sur GitHub | **Interdit comme réparation rapide** sur `main` |

**Règle :** rebase principalement pour des commits locaux non publiés ; évite de réécrire l'historique d'une branche déjà partagée. Pendant un conflit de rebase : modifier le fichier, `git add fichier`, `git rebase --continue`. Pour renoncer : `git rebase --abort`. Pendant un merge : `git merge --abort` ; une fois le conflit résolu, `git add` puis `git commit` si Git ne termine pas automatiquement.

## 6. `stash` : mettre des modifications en sécurité pendant une intervention

`git stash` conserve temporairement les modifications des fichiers suivis ; `-u` inclut aussi les fichiers non suivis (mais **pas** ceux ignorés par `.gitignore`). Une fois le travail à jour, `git stash apply` les réapplique ; `git stash pop` les réapplique **et supprime l'entrée si l'opération réussit**.

```bash
# À comprendre, non à exécuter par réflexe
# 1) Vérifier ce qui va être mis de côté
git status -sb
# 2) En cas de besoin réel
git stash push -u -m "Before repository synchronization"
# 3) Mettre la branche à jour, puis restaurer prudemment
git stash list
git stash apply stash@{0}
git status -sb
# git stash drop stash@{0}   # uniquement après contrôle de la restauration
```

**Pourquoi c'était utile sur ton Z4 :** le répertoire contenait un PDF, des embeddings `.npz`, des fichiers temporaires, des modifications JSON et huit suppressions locales. La mise à jour devait préserver ces éléments **sans les envoyer sur GitHub**. Avant un `stash -u`, fais attention à la taille des gros fichiers et à la nature des documents ; un stash n'est **pas** une sauvegarde distante.

## 7. `.gitignore`, secrets et fichiers volumineux

Ton dépôt est **public**. Le fichier [`.gitignore` à la racine](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/.gitignore) exclut notamment `.venv/`, `__pycache__/`, `*.safetensors`, `.env`, `*.zip` et certains dossiers de sauvegarde. Il ne couvre **pas automatiquement** tous les PDF, toutes les sorties `.npz` et tous les sous-dossiers `models/`. Le [`.gitignore` de B5](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/.gitignore) protège son `.env` et son environnement Python.

**Pourquoi ne pas tout pousser :** les fichiers de code, notebooks nettoyés, schémas SQL, tests et README prouvent davantage tes compétences que des poids de modèle, caches ou documents internes. Un notebook peut contenir des résultats de cellules, des chemins personnels et des valeurs confidentielles.

Contrôles utiles avant un commit :

```bash
git diff --cached --name-status
git diff --cached --check
git diff --cached --stat
git check-ignore -v chemin/vers/fichier   # explique une règle d'exclusion
git ls-files --error-unmatch chemin/vers/fichier  # indique si Git suit déjà le fichier
```

**Attention :** `.gitignore` n'enlève pas le suivi d'un fichier déjà committé. `git rm --cached fichier` le retire de l'index **et planifie sa suppression du dépôt au prochain commit**, tout en gardant le fichier sur ton disque. Pour une clé secrète déjà publiée, supprimer le fichier du dernier commit ne suffit pas : il faut aussi révoquer/faire tourner la clé et évaluer l'historique.

## 8. SSH sur ton Z4 : une leçon de diagnostic, pas un cours de clés

Tu utilisais `git@github.com:Mircea11/BF_IntegIA_2026.git`. Pendant la panne, `ssh -vvv` a montré que GitHub reconnaissait la clé mais que la demande de signature passait par `/run/user/1000/gcr/ssh`. La clé utilisable directement était `~/.ssh/github_formation` ; l'autre clé `key11-09-26` demandait une passphrase que tu n'avais pas validée pendant le test. L'accès SSH a finalement fonctionné sur `ssh.github.com:443` avec `IdentityAgent=none`.

```bash
# Exemple de la connexion ayant fonctionné sur ton environnement :
ssh -T -p 443 -o IdentityAgent=none \
    -o IdentitiesOnly=yes \
    -i ~/.ssh/github_formation \
    git@ssh.github.com
```

Une connexion SSH authentifiée donne normalement une salutation GitHub indiquant qu'aucun shell interactif n'est fourni. **Ne publie jamais le contenu d'une clé privée.** Une clé publique `.pub` est faite pour être partagée avec le service d'authentification ; la passphrase reste privée.

La méthode de push exceptionnelle que tu as utilisée passait `GIT_SSH_COMMAND` pour **une seule commande**. Elle n'a pas à être transformée en configuration permanente pour le cours. L'objectif est surtout de reconnaître trois échecs différents : réseau, authentification, divergence Git.

## 9. Branches, conflits et pull requests

Le support de ton collègue décrit un exercice avec branches `dev`, `test`, `test2`, changements concurrents, `revert` et trois pull requests. **Ce sont des éléments du support, non des actions vérifiées sur ton dépôt.** Pour un futur projet :

```bash
git switch -c feature/controle-donnees   # branche locale nouvelle
git status -sb
# apporter des modifications, tester, indexer et committer
git switch main
git merge feature/controle-donnees
```

Une **pull request** ouvre une demande de revue et de fusion sur GitHub : elle facilite la discussion, les tests et la traçabilité. Tu peux aussi utiliser des branches pour séparer une expérimentation B5 de la branche stable `main`.

Un **conflit** survient si des modifications incompatibles portent sur les mêmes lignes :

```text
<<<<<<< HEAD
mode = "validation"
=======
mode = "analyse"
>>>>>>> feature/analyse
```

Tu dois choisir ou combiner les changements, **supprimer les marqueurs**, vérifier le résultat puis `git add` et terminer le merge/rebase. Ne jamais exécuter automatiquement `reset --hard`, `push --force` ou `rebase --skip` pour faire « disparaître » un conflit.

## 10. Laboratoire sans risque — 3 × 45 minutes

**Tous les exercices d'écriture se déroulent dans un dépôt temporaire indépendant, pas dans `~/formation`. Aucun `push`, aucune modification de `main`.** Si tu fermes le terminal, le dossier temporaire demeure jusqu'au nettoyage de `/tmp` : copie tes notes utiles dans un fichier d'étude, sans données privées.

### Bloc A — Créer trois commits et lire l'index (45 min)

```bash
LAB=$(mktemp -d /tmp/git-cours10-XXXXXX)
printf '%s\n' "$LAB" > /tmp/git-cours10-dernier-chemin.txt
cd "$LAB"
git init -b main
git config user.name "Formation Git"
git config user.email "formation@example.invalid"

printf 'stock = 0\nprint(stock > 0)\n' > produit.py
git status -sb
git add produit.py
git diff --cached --name-status
git commit -m "Add basic stock availability example"

printf 'prix = 11.99\n' >> produit.py
git diff
git add produit.py
git commit -m "Add catalogue price example"
git log --oneline --graph
```

**Sans aide, explique :** pourquoi le second `printf` est visible par `git diff` mais pas dans le premier commit ; pourquoi `git status` est propre après le second commit ; pourquoi aucun de ces fichiers n'est sur GitHub.

### Bloc B — Créer et résoudre volontairement un conflit (45 min)

À exécuter **dans le même dossier temporaire du bloc A** :

```bash
git switch main
printf 'mode = "initial"\n' > configuration.py
git add configuration.py
git commit -m "Add initial configuration"

git switch -c feature/analyse
printf 'mode = "analyse"\n' > configuration.py
git add configuration.py
git commit -m "Select analysis mode"

git switch main
printf 'mode = "validation"\n' > configuration.py
git add configuration.py
git commit -m "Select validation mode"

git merge feature/analyse  # conflit attendu : ce n'est pas un échec de l'exercice
```

Ouvre `configuration.py`, lis les marqueurs, puis remplace le fichier par une résolution justifiée :

```bash
printf 'mode = "validation_et_analyse"\n' > configuration.py
git add configuration.py
git commit -m "Resolve configuration mode conflict"
git log --oneline --graph --all
```

**À prouver :** tu peux expliquer les deux propositions en conflit, justifier ta résolution et retrouver le commit de fusion dans l'historique.

### Bloc C — Auditer ton vrai dépôt sans le modifier (45 min)

Retour au dépôt de formation, **lecture seule** :

```bash
cd ~/formation
git status -sb
git log -6 --oneline --graph --decorate
git show --stat --oneline c17017e
git ls-files N8N/B5_conseiller_produit_v2
```

Compare ensuite le commit `c17017e` à son prédécesseur distant `8ce79ce` depuis l'interface GitHub. Identifie les 10 fichiers B5, les 3 rapports n8n et les 5 fichiers RAG ajoutés/modifiés. Les numéros courts de SHA sont suffisants tant qu'ils ne sont pas ambigus.

**Livrable portfolio (pas à publier automatiquement) :** une note de 10 lignes expliquant comment tu as sélectionné 18 fichiers, évité les suppressions, résolu la divergence GitHub et vérifié la publication. Elle peut devenir un paragraphe technique de ton showroom professionnel.

## 11. Autotest — réponds avant de lire le corrigé

1. Git et GitHub sont-ils le même outil ?
2. Quelles sont les trois zones locales (avant le distant) ?
3. Que signifie `??` dans `git status -sb` ?
4. Un `git commit` réussi prouve-t-il que GitHub possède les fichiers ?
5. Quelle commande montre exactement les changements qui vont entrer dans le prochain commit ?
6. Comment retirer un fichier de l'index sans supprimer son contenu local ?
7. Pourquoi ton `push` a-t-il été rejeté avec `fetch first` ?
8. Que signifie le passage de `ba0f8ed` à `c17017e` ?
9. Pourquoi `git push --force` était-il dangereux dans ton cas ?
10. Quand utiliser `git stash -u`, et quels fichiers n'inclut-il pas ?
11. Le fait d'ajouter `.env` à `.gitignore` protège-t-il une clé déjà publiée ?
12. Comment distinguer un conflit Git d'un problème d'authentification SSH ?

### Corrigé et critères

1. Non : Git versionne localement ; GitHub héberge et facilite la collaboration.
2. Répertoire de travail → index (*staging*) → historique local.
3. Fichier non suivi, nouveau pour Git.
4. Non : il faut un `push` réussi, puis vérifier le serveur ou le suivi distant mis à jour.
5. `git diff --cached` (`--name-status` pour la liste et le statut des fichiers).
6. `git restore --staged chemin`.
7. GitHub possédait un commit absent de l'historique local (`8ce79ce`).
8. Le `rebase` a rejoué ton commit local sur la nouvelle base ; il a reçu un autre SHA.
9. Il pouvait remplacer l'historique du serveur et faire perdre le checkpoint distant.
10. Quand on doit dégager un répertoire de travail avant intégration : `-u` ajoute les non suivis, mais pas les fichiers ignorés ; vérifier la taille et les contenus.
11. Non : révoquer le secret et traiter l'historique ; `.gitignore` ne s'applique qu'au suivi futur de fichiers non encore suivis.
12. Conflit : Git signale un merge/rebase et les fichiers en conflit ; authentification : SSH ou GitHub refuse l'identité avant toute intégration.

**Barème personnel :** 0–4/12 = notions à revoir ; 5–8 = compréhension guidée ; 9–11 = bonne compréhension ; 12 + les trois blocs réussis sans aide = autonomie démontrée sur ce périmètre. Ne pas confondre une réponse mémorisée et un exercice exécuté indépendamment.

## 12. Fiche de reprise rapide — avant un vrai push

| Ordre | Question de contrôle | Commande |
|---|---|---|
| 1 | Dans quel dépôt et quelle branche suis-je ? | `pwd && git status -sb` |
| 2 | Que vais-je réellement publier ? | `git diff --cached --name-status` |
| 3 | Ai-je inclus un secret ou un fichier inutile ? | Inspecter diff, notebooks et fichiers staged |
| 4 | Le commit est-il créé localement ? | `git log -1 --oneline` |
| 5 | Le serveur a-t-il avancé depuis ma copie ? | `git fetch origin` puis comparer les branches |
| 6 | Faut-il fusionner ou rebaser ? | Choisir consciemment selon l'historique |
| 7 | Le `push` est-il accepté ? | Lire **le résultat complet** de `git push` |
| 8 | Quelle version est sur GitHub ? | Vérifier le dernier commit dans l'interface GitHub |

> **Pour ton projet professionnel :** la compétence visée n'est pas « connaître 40 commandes par cœur ». C'est savoir **sélectionner, documenter, récupérer et publier un travail de données ou d'IA sans écraser de fichiers ni exposer de secrets**. Les réflexes de Git sont directement transférables à un poste de Data / AI Integration Specialist.

## 13. Sources et limites

**Support de ton collègue (fourni) :** `2026 Cours.zip` → `2026-09-04_08 - Git.md`, période 4–8 septembre 2026. Contient le cours Git, un scénario de branches/PR et des compléments issus du *Git Cheat Sheet* (Tower). Les commandes ont été contextualisées ; les conseils de sécurité et le laboratoire sont des ajouts pédagogiques.

**Sources GitHub vérifiées (26 octobre 2026) :** [dépôt principal](https://github.com/Mircea11/BF_IntegIA_2026) ; [checkpoint `8ce79ce`](https://github.com/Mircea11/BF_IntegIA_2026/commit/8ce79ce44b671b26f9dd1bd3832cda42567e45e9) ; [commit `c17017e`](https://github.com/Mircea11/BF_IntegIA_2026/commit/c17017e8a2ae4f7872ed092747d785d42a6be915) ; [racine `.gitignore`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/.gitignore) ; [workflow et scripts B5](https://github.com/Mircea11/BF_IntegIA_2026/tree/main/N8N/B5_conseiller_produit_v2).
