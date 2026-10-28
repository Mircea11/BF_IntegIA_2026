"""
E09.5-C — PREMIÈRE EXPÉRIENCE MULTIQUESTIONS

OBJECTIF
--------
1. Charger le golden dataset.
2. Sélectionner trois questions.
3. Créer une expérience PostgreSQL.
4. Exécuter la recherche dense.
5. Enregistrer les résultats de chaque question.
6. Marquer l'expérience comme terminée.

Cette version ne calcule pas encore les métriques.
Elles seront ajoutées lors de l'étape suivante.
"""


# ============================================================
# [E09.5-C2 — SECTION 0] IMPORTS
# ============================================================

# Lire les fichiers JSON.
import json

# Mesurer les durées d'exécution.
from time import perf_counter

# Configuration du projet.
from rag_hopital.config import settings

# Fonctions PostgreSQL déjà développées.
from rag_hopital.db import (
    create_experiment,
    save_question_result,
    finish_experiment,
)

# Nom de la collection Qdrant.
from rag_hopital.etl.index import COLLECTION

# Fonction de recherche dense validée en E08.
from rag_hopital.rag.search import search


# ============================================================
# [E09.5-C2 — SECTION 1] CHARGER LES QUESTIONS
# ============================================================

# Construire le chemin du fichier JSON.
path = settings.corpus_path / "hopital_eval.json"

# Lire et convertir le JSON en liste Python.
questions = json.loads(
    path.read_text(encoding="utf-8")
)

# Sélectionner les trois premières questions
# contenant des preuves dans le corpus.
#
# Les questions out_of_corpus seront évaluées séparément.
#
# [:3] conserve les trois premiers éléments.
selected_questions = [
    question
    for question in questions
    if question["type"] != "out_of_corpus"
][:3]

print("Questions sélectionnées :")

for question in selected_questions:
    print(question["id"], "-", question["type"])


# ============================================================
# [E09.5-C2 — SECTION 2] CONFIGURATION
# ============================================================

# Décrire précisément la configuration utilisée.
#
# Cette configuration sera enregistrée dans PostgreSQL.
#
# Elle permettra ensuite de comparer cette expérience
# avec une recherche hybride utilisant les mêmes questions.
config = {
    "name": "dense_3_questions_test",
    "dataset": "hopital_eval.json",
    "question_ids": [
        question["id"]
        for question in selected_questions
    ],
    "method": "dense",
    "embedding_model": "bge-m3",
    "collection": COLLECTION,
    "top_k": 5,
    "reranker": None,
    "generation": None,
}


# ============================================================
# [E09.5-C2 — SECTION 3] CRÉER L'EXPÉRIENCE
# ============================================================

# Démarrer le chronomètre général.
experiment_start = perf_counter()

# Créer une seule expérience PostgreSQL.
#
# La fonction retourne son identifiant.
#
# Cet identifiant sera réutilisé pour les trois questions.
experiment_id = create_experiment(config)

print("\nExpérience créée :", experiment_id)


# ============================================================
# [E09.5-C2 — SECTION 4] EXÉCUTER LES RECHERCHES
# ============================================================

# Parcourir les trois questions sélectionnées.
for question in selected_questions:

    print("\nRecherche :", question["id"])

    # Démarrer le chronomètre de cette question.
    start = perf_counter()

    # Exécuter la recherche dense dans Qdrant.
    #
    # top_k=5 : récupérer les cinq chunks les mieux classés.
    points = search(
        question["question"],
        top_k=5,
    )

    # Calculer le temps de recherche.
    #
    # perf_counter() retourne le temps actuel du chronomètre.
    #
    # La différence donne la durée en secondes.
    #
    # Multiplier par 1000 convertit les secondes
    # en millisecondes.
    latency_ms = (perf_counter() - start) * 1000

    # Enregistrer les résultats dans PostgreSQL.
    #
    # Toutes les questions reçoivent le même experiment_id.
    #
    # Cette fonction écrit dans la table answers.
    save_question_result(
        experiment_id=experiment_id,
        question=question,
        points=points,
        latency_ms=latency_ms,
    )

    print(
        "Temps de recherche :",
        round(latency_ms, 2),
        "ms",
    )


# ============================================================
# [E09.5-C2 — SECTION 5] TERMINER L'EXPÉRIENCE
# ============================================================

# Mesurer la durée totale.
#
# Elle comprend les recherches et les opérations
# d'enregistrement effectuées pendant l'expérience.
duration_s = perf_counter() - experiment_start

# Modifier le statut PostgreSQL : running -> done.
finish_experiment(
    experiment_id=experiment_id,
    duration_s=duration_s,
)


# ============================================================
# [E09.5-C2 — SECTION 6] AFFICHER LE BILAN
# ============================================================

print("\n=== EXPÉRIENCE TERMINÉE ===")

print("Experiment ID :", experiment_id)

print("Questions traitées :", len(selected_questions))

print("Méthode :", config["method"])

print("Collection :", COLLECTION)

print("Durée totale :", round(duration_s, 2), "secondes")

print("Résultats enregistrés dans PostgreSQL.")