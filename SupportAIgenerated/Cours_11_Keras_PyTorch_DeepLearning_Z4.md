# Cours personnel 11 — Deep learning avec Keras et PyTorch

**Formation AI Integration Specialist · Consolidation personnelle · 26 octobre 2026**  
**Support principal :** `2026-09-09_16 - Keras et PyTorch.md` dans `2026 Cours.zip` (notes du module des 9, 10, 11, 15 et 16 septembre).  
**Références personnelles :** notebooks et fichiers présents dans `Mircea11/BF_IntegIA_2026`, vérifiés sur GitHub le 26 octobre 2026.  
**Durée prévue :** 75–95 min de lecture, puis trois blocs de 45 min et un autotest de 15 min.  
**Prérequis :** Python et NumPy (cours 02), classes (cours 06), visualisation (cours 05), LLM (cours 09).  
**Finalité :** lire et expliquer un entraînement, comparer deux modèles et interpréter leurs résultats avant de chercher à les optimiser.

> **Niveau de preuve.** Ton dépôt contient des notebooks qui construisent des modèles Keras, des cellules exécutées et des exercices commentés. Cela prouve la présence de travaux d'apprentissage. Ce n'est pas une preuve que tu sais les reconstruire **seul**. Les exercices ci-dessous évaluent ce passage vers l'autonomie. Le support de ton collègue cite en outre des dossiers de cours `keras/`, `torch/` et `deeplearning_full/` qui ne correspondent pas exactement à l'arborescence vérifiée de ton dépôt GitHub. Les références personnelles utilisées ici pointent uniquement vers des chemins vérifiés.

## 1. À quoi sert ce cours dans ta trajectoire ?

Tu as déjà travaillé avec des **modèles pré-entraînés** : Nemotron pour produire/interpréter du texte et BGE-M3 pour calculer des embeddings, servis via vLLM. **Servir un modèle** consiste à appliquer des poids déjà appris à une entrée. **Entraîner un modèle** consiste à modifier ces poids à partir d'exemples et d'une fonction de coût. Ce sont deux métiers techniques liés mais différents.

| Dans tes projets | Ce que tu fais / observes | Ce que ce cours ajoute |
|---|---|---|
| B5 : conseiller produit | Appels à Nemotron, embeddings BGE-M3, stock contrôlé par l'API | Comprendre d'où viennent les poids d'un modèle et pourquoi les résultats doivent être évalués |
| RAG : extraction et recherche | Documents → chunks → vecteurs → requêtes | Comprendre que les vecteurs proviennent d'un modèle appris, sans entraîner BGE-M3 toi-même |
| `deeplearning/deeplearning1/` | Notebooks de classification d'images avec Keras | Comprendre les étapes `compile`, `fit`, `evaluate` et la généralisation |
| Positionnement professionnel | Intégration IA, qualité des données, décision | Pouvoir choisir un modèle existant, vérifier les métriques et documenter ses limites |

**Priorité :** pour ton objectif professionnel, la capacité de **comprendre, évaluer et intégrer** des modèles apporte actuellement plus de valeur que l'entraînement d'un grand modèle sur ton GPU. La formation aux CNN donne des bases transférables pour auditer un pipeline IA.

## 2. Le neurone artificiel et l'apprentissage

Un neurone combine ses entrées puis applique une fonction d'activation :

```text
Entrées x1, x2 → somme z = w1·x1 + w2·x2 + b → activation(z) → prédiction
                                                         │
Valeur attendue ── comparaison ── perte (loss) ←───────────┘
                          │
                   calcul des gradients
                          │
                 mise à jour des poids
```

Les **poids** (`w1`, `w2`) règlent l'importance des entrées. Le **biais** (`b`) décale la sortie. La **fonction d'activation** ajoute de la non-linéarité. La **fonction de coût** mesure l'écart entre prédictions et valeurs attendues.

**Exemple numérique issu de la logique du support :** `x1 = 2`, `x2 = 0,5`, `w1 = 0,2`, `w2 = 0,3`, `b = 0`. Alors `z = 2×0,2 + 0,5×0,3 = 0,55`. Si l'on suppose une sortie **linéaire** et une cible `1`, l'écart signé est `1 − 0,55 = 0,45`. **L'écart n'est pas automatiquement la loss** : avec l'erreur quadratique, la perte d'un exemple serait `(1 − 0,55)² = 0,2025`.

**Forward pass** : la prédiction est calculée, sur un exemple ou un lot (*batch*). **Backpropagation** : les dérivées de la perte sont propagées pour mesurer l'effet de chaque poids. **Optimiseur** : il modifie les poids, par exemple avec la descente de gradient :

```text
nouveau_poids = ancien_poids − learning_rate × gradient
```

Le gradient indique la pente **locale**. Il ne garantit pas à lui seul une amélioration globale après un grand pas. C'est pourquoi le *learning rate* doit être réglé.

### Pourquoi les activations comptent

Sans activation non linéaire, plusieurs couches linéaires successives restent équivalentes à une seule transformation linéaire. Avec des activations, le réseau peut apprendre des relations complexes. Les notes de ton collègue discutent notamment :

| Activation | Définition / effet | À retenir |
|---|---|---|
| ReLU | `max(0, x)` | Simple et fréquente ; risque de neurones inactifs pour des entrées toujours négatives |
| Leaky ReLU | Garde une faible pente sous zéro | Réduit le risque de gradient nul du côté négatif |
| SiLU | `x × sigmoid(x)` | Courbe lisse ; utilisée dans diverses architectures modernes |
| Sigmoïde | Valeurs entre 0 et 1 | Pratique pour une **sortie binaire** |
| Softmax | Probabilités normalisées entre plusieurs classes | Pratique pour une **sortie multiclasse exclusive** |

**Vérification mathématique du support :** `sigmoid(-0,4) ≈ 0,4013`, et non `0,4625`. La correction figure également dans la note de ton collègue. Distingue toujours la **source**, son **exemple pédagogique** et le calcul réellement vérifié.

## 3. Ce que veulent dire epoch, batch et learning rate

Sur **240 observations** avec un batch de **24**, une epoch comporte normalement **10 lots**, donc environ **10 mises à jour** si l'optimiseur met à jour les poids après chaque lot. Cinq epochs représentent alors environ 50 étapes d'optimisation (hors particularités d'implémentation).

| Mot | Définition | Erreur fréquente |
|---|---|---|
| *Epoch* | Passage complet sur le jeu d'entraînement | Croire qu'une epoch = un seul calcul de gradient |
| *Batch size* | Nombre d'exemples utilisés par mise à jour | Prendre le batch maximal en GPU pour forcément obtenir le meilleur modèle |
| *Learning rate* | Amplitude des mises à jour | Le confondre avec le nombre d'epochs |
| *Loss* | Fonction à minimiser | La confondre avec l'accuracy |
| *Accuracy* | Part des prédictions correctes | L'utiliser seule avec des classes très déséquilibrées |

**Mise à l'échelle** : selon l'usage courant de scikit-learn, **standardiser** correspond à centrer/réduire (moyenne 0, écart-type 1) ; **normaliser par MinMax** consiste à ramener les données dans un intervalle. Le vocabulaire varie, mais le code utilisé doit être explicite. Pour des images 8 bits, `Rescaling(1./255)` ramène les pixels de 0–255 à 0–1.

## 4. Keras 3 avec backend PyTorch : deux niveaux à ne pas mélanger

Le support de ton collègue utilise **Keras 3**, avec le moteur **PyTorch** sélectionné avant l'import. Les notebooks commentés de ton dépôt font la même chose :

```python
import os
os.environ["KERAS_BACKEND"] = "torch"  # AVANT import keras
import keras

print(keras.backend.backend())  # attendu : torch
```

**Keras** décrit les couches, les modèles et la boucle d'apprentissage à haut niveau. **PyTorch backend** effectue les calculs en dessous. Ce n'est **pas** la même syntaxe que l'API PyTorch native (`torch.nn.Module`, `forward`, `loss.backward()`, `optimizer.step()`). La distinction est importante à l'entretien : ne pas affirmer avoir programmé un entraînement *PyTorch natif* si l'on a utilisé Keras avec le backend `torch`.

Pour vérifier les capacités locales, sans lancer d'entraînement :

```python
import torch
print("CUDA disponible :", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU :", torch.cuda.get_device_name(0))
```

Ces commandes **constatent** la disponibilité de CUDA à l'instant du test ; la présence du script dans GitHub ne prouve pas que ton Z4 est actuellement prêt ou que l'environnement Python actif contient les bonnes versions.

**Référence personnelle vérifiée :** [Fashion-MNIST commenté](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/Carl_fashion_mnist_clean_commented.ipynb), [dépendances `pyproject.toml`](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/pyproject.toml).

## 5. Lire une expérience d'entraînement complète

Un entraînement bien organisé suit la séquence : **charger → comprendre → séparer → préparer → définir → compiler → entraîner → comparer → évaluer → documenter**.

### 5.1 Les trois jeux de données

- **Entraînement** : fournit les exemples qui servent à changer les poids.
- **Validation** : suit la généralisation et sert à choisir les paramètres d'entraînement.
- **Test** : conserve une évaluation finale indépendante ; on n'y règle pas le modèle.

Dans Fashion-MNIST, le jeu officiel contient **60 000 images côté entraînement** et **10 000 images de test**. Le notebook vérifié découpe les 60 000 en **48 000 entraînement + 12 000 validation**. Dans CIFAR-10, il s'agit de **50 000 côté entraînement + 10 000 test**, avec une séparation **40 000 / 10 000** entre entraînement et validation. Il faut garder les mêmes découpages pour comparer les architectures.

**Risque de fuite de données (*data leakage*) :** si les observations du test influencent le choix d'architecture, de seuil ou de nombre d'epochs, le score final devient trop optimiste. En production industrielle, pense aussi aux duplications, aux lots d'une même usine et aux données temporelles qui peuvent contaminer plusieurs sous-ensembles.

### 5.2 Modèle Dense : ce que le code exprime

```python
from keras import Input, Sequential, layers

modele = Sequential([
    Input(shape=(28, 28)),
    layers.Rescaling(1.0 / 255),
    layers.Flatten(),                  # 28 × 28 → 784 valeurs
    layers.Dense(64, activation="relu"),
    layers.Dense(10, activation="softmax"),
])
modele.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
modele.summary()
```

Ce modèle correspond à une **classification en dix classes** dont les étiquettes sont des entiers `0…9`. Il traite l'image comme un vecteur plat de 784 valeurs : il ne conserve pas explicitement la proximité des pixels. Sa première couche Dense de 64 neurones contient `(784 × 64) + 64 = 50 240 paramètres`.

| Problème | Sortie adaptée | Perte courante |
|---|---|---|
| Régression (valeur continue) | 1 neurone linéaire | `mse` |
| Deux classes exclusives | 1 neurone `sigmoid` | `binary_crossentropy` |
| Plusieurs classes, labels entiers | `n` neurones `softmax` | `sparse_categorical_crossentropy` |
| Plusieurs classes, labels one-hot | `n` neurones `softmax` | `categorical_crossentropy` |

**À contrôler dans tes notebooks :** formes `X.shape` et `y.shape`, cohérence entre activation de sortie et loss, et position de la normalisation pour éviter de la faire deux fois.

### 5.3 Entraîner, observer, évaluer

```python
historique = modele.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=10,
    batch_size=32,
    verbose=1,
)

score_test = modele.evaluate(X_test, y_test, verbose=0)
print(historique.history.keys())
print(score_test)
```

Cet extrait suppose que tu as **déjà préparé** `X_train`, `X_val`, `X_test` et leurs labels. Ne le lance pas directement sans données. Les clés habituelles de l'historique sont `loss`, `val_loss`, `accuracy`, `val_accuracy`. Les courbes sont plus instructives qu'un seul chiffre.

## 6. Dense contre CNN : pourquoi l'architecture importe

**CNN** = *Convolutional Neural Network*. Un filtre parcourt une image et apprend des motifs locaux (bords, textures, formes). Une couche `Conv2D(64, 3)` produit **64 cartes de caractéristiques**, pas `nombre_de_canaux_entrants × 64` cartes.

Exemple simplifié pour des images RGB de forme `(32, 32, 3)` :

```python
cnn = Sequential([
    Input(shape=(32, 32, 3)),
    layers.Rescaling(1.0 / 255),
    layers.Conv2D(64, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(2),
    layers.Conv2D(128, 3, padding="same", activation="relu"),
    layers.GlobalAveragePooling2D(),
    layers.Dense(10, activation="softmax"),
])
```

**Calcul vérifiable :** pour la première convolution, `((3 × 3 × 3) + 1) × 64 = 1 792 paramètres` si chaque filtre possède un biais. `MaxPooling2D(2)` réduit les dimensions spatiales en gardant un maximum local ; ce n'est pas une convolution entraînable. `GlobalAveragePooling2D` produit une valeur par carte, évitant une grande couche dense après `Flatten`.

**Référence personnelle vérifiée :** [CIFAR-10 commenté](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/cifar10_clean_commented.ipynb). Ce notebook compare une baseline Dense et un CNN, examine les courbes et propose une expérience optionnelle de régularisation.

## 7. Diagnostiquer le surapprentissage : priorité à la preuve

| Ce que montrent les courbes | Interprétation possible | Décision prudente |
|---|---|---|
| `loss` et `val_loss` baissent | Apprentissage et validation progressent | Continuer sous contrôle |
| `loss` baisse, `val_loss` monte | Surapprentissage probable | Examiner données, réduire complexité, essayer régularisation |
| `loss` et `val_loss` restent élevées | Sous-apprentissage ou erreur de configuration | Vérifier labels, prétraitement, loss et architecture |
| Accuracy élevée mais classes rares mal reconnues | Métrique trompeuse | Consulter matrice de confusion, précision, rappel par classe |

**Régularisation** selon le support : augmentation d'images (`RandomFlip`, etc.), `Dropout`, réduction de paramètres, *early stopping*. Rien n'impose d'activer tout simultanément. Comparer **baseline → une modification → nouvel entraînement**, avec données identiques.

```python
from keras.callbacks import EarlyStopping, ModelCheckpoint

callbacks = [
    EarlyStopping(monitor="val_loss", patience=4,
                  restore_best_weights=True),
    ModelCheckpoint("best_model.keras", monitor="val_loss",
                    save_best_only=True),
]
```

**Attention à `min_delta` :** fixer `min_delta=0.2` pour une validation-loss évoluant par centièmes peut empêcher de reconnaître des améliorations réelles. Dans ton notebook de régularisation, ce paramètre a fait l'objet d'une analyse explicite. Ne le recopies pas sans regarder l'ordre de grandeur de la loss.

**Référence personnelle vérifiée :** [Régularisation — visualisation et annotations](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/Regularisation_4_visual_annotated_learning.ipynb). Des cellules annotées et des valeurs sauvegardées dans un notebook ne remplacent pas un benchmark reconduit sur le Z4.

## 8. API fonctionnelle, transfert et autres architectures : connaître leur rôle

Le support approfondit ensuite des cas avancés. Ils sont à **reconnaître et expliquer**, pas à transformer immédiatement en nouveaux projets.

| Concept du support | Principe | Lien possible avec tes projets |
|---|---|---|
| API fonctionnelle Keras | Plusieurs branches, fusions, connexions, via `keras.Model` | Lire les architectures Inception-like de tes notebooks |
| *Transfer learning* (VGG16, ResNet) | Réutiliser un extracteur préentraîné ; souvent geler d'abord ses poids | Choisir un modèle existant plutôt que tout réentraîner |
| Autoencodeur, U-Net | Compresser/reconstruire, parfois débruiter ou segmenter | Comprendre les représentations latentes |
| Réseau siamois | Deux entrées via des poids partagés ; apprendre une similarité | Mettre en relation le concept d'embedding avec RAG |
| CNN 1D / RNN | Analyser des séquences ou séries temporelles | Lien futur avec données de production et prévisions |
| GAN / renforcement | Génération adversariale / décisions fondées sur une récompense | Culture générale ; hors du chemin prioritaire actuel |

**Précision essentielle :** les embeddings de BGE-M3 utilisés par Qdrant et les représentations apprises par un réseau siamois suivent une idée générale de **similarité entre vecteurs**. Cela ne signifie pas que tes deux projets utilisent le même modèle, la même fonction de perte ou les mêmes données.

## 9. Laboratoire court, sans téléchargement : un neurone et son gradient

Ce premier script utilise seulement Python et **NumPy**, déjà rencontré dans la formation. Il illustre concrètement la mise à jour d'un poids, sans entraîner un modèle volumineux ni toucher aux services vLLM actifs.

```python
import numpy as np

x = np.array([2.0, 0.5])
w = np.array([0.2, 0.3])
b = 0.0
cible = 1.0
learning_rate = 0.1

prediction = np.dot(x, w) + b
perte_avant = (prediction - cible) ** 2

gradient_w = 2 * (prediction - cible) * x
gradient_b = 2 * (prediction - cible)

w = w - learning_rate * gradient_w
b = b - learning_rate * gradient_b

prediction_apres = np.dot(x, w) + b
perte_apres = (prediction_apres - cible) ** 2

print("Prédiction avant :", round(float(prediction), 4))
print("Prédiction après :", round(float(prediction_apres), 4))
print("Perte avant :", round(float(perte_avant), 4))
print("Perte après :", round(float(perte_apres), 4))
assert perte_apres < perte_avant
```

**Résultats de référence de ce script :** prédiction initiale `0,55` ; gradient des poids `[-1,8, -0,45]` ; poids corrigés `[0,38, 0,345]` ; biais corrigé `0,09` ; nouvelle prédiction `1,0225` ; perte finale `0,00050625`. Ce n'est qu'**un exemple à un seul neurone et un seul échantillon**. En vrai entraînement, le comportement peut être beaucoup moins simple.

## 10. Exercice optionnel Keras : mini-modèle sur données générées

**Ne pas installer de paquets ni télécharger de données sans nécessité.** Dans ton environnement déjà opérationnel de deep learning, ce code peut être exécuté dans un nouveau notebook pour isoler la mécanique de la dépendance à Fashion-MNIST ou CIFAR-10 :

```python
import os
os.environ["KERAS_BACKEND"] = "torch"  # redémarrer le kernel si keras a déjà été importé
import numpy as np
import keras
from keras import Sequential, Input, layers

keras.utils.set_random_seed(42)
rng = np.random.default_rng(42)
X = rng.normal(size=(240, 2)).astype("float32")
y = (X[:, 0] + 0.6 * X[:, 1] > 0.25).astype("float32")

# Séparation déterministe : 160 train, 40 validation, 40 test.
X_train, X_val, X_test = X[:160], X[160:200], X[200:]
y_train, y_val, y_test = y[:160], y[160:200], y[200:]

modele = Sequential([
    Input(shape=(2,)),
    layers.Dense(8, activation="relu"),
    layers.Dense(1, activation="sigmoid"),
])
modele.compile(optimizer="adam", loss="binary_crossentropy",
               metrics=["accuracy"])
historique = modele.fit(X_train, y_train, validation_data=(X_val, y_val),
                       epochs=15, batch_size=16, verbose=0)
print(modele.evaluate(X_test, y_test, verbose=0))
print("Dernière val_loss :", historique.history["val_loss"][-1])
```

**Ce script est un exercice proposé**, pas un résultat déjà exécuté sur ton Z4. Les performances dépendent des versions et de l'environnement. Il permet de contrôler séparément : **forme des données → architecture → choix de loss → apprentissage → validation → test**. N'en conclus pas qu'un grand réseau est toujours préférable ; cette tâche pourrait aussi se résoudre par un classifieur linéaire.

## 11. Trois blocs de travail (45 minutes chacun)

### Bloc A — Lire TON notebook Fashion-MNIST, sans exécuter

1. Ouvre `deeplearning/deeplearning1/Carl_fashion_mnist_clean_commented.ipynb` sur GitHub ou sur le Z4.
2. Identifie et explique : `KERAS_BACKEND`, `train_test_split`, `Rescaling`, `Flatten`, `Dense`, `compile`, `fit`, `evaluate`.
3. Dessine une table à trois colonnes : **ligne de code / rôle / ce qui échouerait si elle était absente**.
4. Sans aide, calcule combien de paramètres contient `Dense(64)` recevant 784 entrées.

**Livrable :** une fiche d'une page et le calcul **50 240**, correctement expliqué. **Compétence testée :** lecture de code autonome, pas entraînement GPU.

### Bloc B — Écrire, modifier, vérifier

1. Exécute le laboratoire NumPy de la section 9, puis **réécris-le sans copier** dans une cellule vide.
2. Change seulement le *learning rate* de `0,1` à `0,01` et compare les pertes ; formule une hypothèse avant l'exécution.
3. Si l'environnement Keras fonctionne déjà, essaie le mini-modèle de la section 10 et trace `loss` contre `val_loss` avec Matplotlib.
4. Indique pour chaque résultat « **constaté** » ou « **supposé** ».

**Livrable :** mini-notebook avec entrée, résultat, hypothèse, mesure. **Compétence testée :** comprendre une mise à jour de poids et une courbe de validation.

### Bloc C — Comparer deux modèles sur un protocole stable

1. Parcours `cifar10_clean_commented.ipynb` ; relève les deux architectures comparées : Dense et CNN.
2. Note les valeurs et règles de **train / validation / test**, sans les modifier.
3. Rédige un tableau **architecture / données / métrique / risque de surapprentissage / coût de calcul**. Si aucune mesure vérifiée n'est disponible, écris **« non mesuré »**.
4. Propose **une seule** modification de régularisation (Dropout **ou** augmentation **ou** EarlyStopping), explique quel signal des courbes motiverait ce choix.

**Livrable :** une courte *model card* comparative. **Compétence testée :** expérimentation contrôlée et interprétation, très utile pour ton futur portfolio.

## 12. Autoévaluation — répondre sans ChatGPT

1. Quelle différence entre servir Nemotron avec vLLM et entraîner un modèle Keras ?
2. Quel rôle distinct ont le forward pass, la loss, le backward pass et l'optimiseur ?
3. Pourquoi plusieurs couches purement linéaires ne constituent-elles pas un réseau non linéaire ?
4. Pour 240 observations et des batchs de 24, combien de mises à jour environ par epoch ?
5. Pourquoi séparer entraînement, validation et test ?
6. Que signifie `KERAS_BACKEND="torch"` ? Est-ce du code PyTorch natif ?
7. Que signifie `Input(shape=(28, 28))` ? Le batch fait-il partie de cette forme ?
8. Combien de paramètres pour une couche Dense de 10 sorties recevant 4 entrées (avec biais) ?
9. Quelle association sortie/loss choisir pour dix classes avec des étiquettes entières ?
10. Quelle situation indique un possible surapprentissage ?
11. Pourquoi une convolution est-elle adaptée aux images ?
12. Pourquoi faut-il comparer une baseline à une version régularisée avant de conclure ?

### Corrigé bref

1. **Inférence** : utiliser des poids préexistants ; **entraînement** : ajuster les poids sur des exemples. 2. Prédire ; mesurer erreur ; calculer gradients ; corriger poids. 3. La composition de transformations linéaires reste linéaire. 4. **10**. 5. Apprendre, sélectionner et vérifier indépendamment. 6. Keras exécute ses calculs sur PyTorch ; ce n'est pas l'API native `torch.nn`. 7. Forme d'un exemple ; batch exclu. 8. `4×10 + 10 = 50`. 9. `Dense(10, softmax)` et perte `sparse_categorical_crossentropy`. 10. La loss d'entraînement descend pendant que la validation se dégrade. 11. Elle exploite voisinages et poids partagés. 12. Pour mesurer l'effet d'une modification isolée sur le même protocole.

**Échelle d'autonomie :** *A* = je reconnais le concept ; *B* = je l'explique ; *C* = je peux l'exécuter sans copie ni aide ; *D* = je peux détecter une erreur et justifier une correction. Pour cette étape, vise **B partout et C sur le laboratoire NumPy**. Ne déduis pas D de la simple présence de notebooks dans GitHub.

## 13. Sources et points de contrôle

**Support fourni (source principale)** : `2026 Cours.zip` → `2026-09-09_16 - Keras et PyTorch.md`. Ce document synthétise les notes de formation, les couches Keras, le backend PyTorch, Fashion-MNIST, CIFAR-10, régularisation, API fonctionnelle, transfer learning et architectures plus avancées. Ses corrections internes sont signalées lorsqu'elles changent l'interprétation d'un exemple.

**Sources personnelles vérifiées dans GitHub, branche `main` (26.10.2026)** :

- [Fashion-MNIST, version commentée](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/Carl_fashion_mnist_clean_commented.ipynb) : backend Keras/Torch, découpage, baseline Dense, CNN, évaluations et commentaires.
- [CIFAR-10, version commentée](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/cifar10_clean_commented.ipynb) : formes RGB, baseline Dense, CNN, validation et inspection de filtres.
- [Régularisation et analyses visuelles](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/Regularisation_4_visual_annotated_learning.ipynb) : augmentation, callbacks, `val_loss` et limites de `min_delta`.
- [Configuration des dépendances](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/deeplearning/deeplearning1/pyproject.toml) : versions déclarées et exigences de l'environnement, **pas** preuve de l'installation actuelle.
- [B5 — code d'intégration des modèles](https://github.com/Mircea11/BF_IntegIA_2026/blob/main/N8N/B5_conseiller_produit_v2/app.py) : application qui **utilise** Nemotron et BGE-M3 ; ne les entraîne pas.

**Limites de vérification :** les exemples ont été revus dans les fichiers du dépôt ; aucun nouvel entraînement Keras n'a été exécuté sur ton Z4 durant la création de ce cours. Les mesures de performances que tu obtiendras lors du travail personnel devront être enregistrées avec la version de Keras, le backend et le matériel utilisé.

---

**Prochain cours : 12 — Servir un LLM avec llama.cpp et vLLM.** Il sera directement lié aux services Nemotron et BGE-M3 que tu as configurés, aux endpoints HTTP et aux limites de VRAM.
