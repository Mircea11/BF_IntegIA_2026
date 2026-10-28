"""
E09.2 — ÉVALUATION D'UNE QUESTION RAG (Q001)

OBJECTIF
--------
1. Lire une expérience déjà enregistrée dans PostgreSQL.
2. Récupérer les chunks correspondants dans Qdrant.
3. Comparer les chunks aux preuves du formateur.
4. Calculer les métriques Hit@k, RR@5 et nDCG@5.
5. Enregistrer les résultats dans PostgreSQL.
6. Afficher les résultats pour vérification.

IMPORTANT
---------
Ce script ne lance PAS une nouvelle recherche.

Il analyse les résultats déjà enregistrés dans
l'expérience n° 1 : dense_Q001_test.

Ce script concerne uniquement Q001.
Il sera généralisé aux 100 questions dans une étape ultérieure.
"""


# ============================================================
# [E09.2 — SECTION 0] IMPORTATION DES BIBLIOTHÈQUES
# ============================================================

# Permet de communiquer avec PostgreSQL.
import psycopg

# Permet de lire les fichiers JSON.
import json

# Permet de reconstruire les identifiants des points Qdrant.
from uuid import uuid5, NAMESPACE_URL

# Paramètres du projet : chemins, connexions et services.
from rag_hopital.config import settings

# Fonction permettant de récupérer une expérience PostgreSQL.
from rag_hopital.db import get_results

# Connexion Qdrant et nom de la collection contenant nos chunks.
from rag_hopital.etl.index import COLLECTION, connect_qdrant

# Fonctions d'évaluation développées dans metrics.py.
#
# judge_chunk :
#     Vérifie si un chunk contient une preuve du golden dataset.
#
# ndcg_at_k :
#     Mesure la qualité du classement des chunks.
from rag_hopital.evaluation.metrics import (
    judge_chunk,
    ndcg_at_k,
    required_facts,
)

from rag_hopital.evaluation.metrics import (
    judge_chunk,
    ndcg_at_k,
    required_facts,
    evaluate_fact_coverage,
)
# ============================================================
# [E09.2 — SECTION 1] CHARGEMENT DU GOLDEN DATASET
# ============================================================

# Le golden dataset contient les 106 questions du formateur.
#
# Chaque question contient notamment :
# - id       : identifiant de la question ;
# - type     : catégorie de la question ;
# - question : texte de la question ;
# - answer   : réponse attendue ;
# - evidence : documents et extraits justificatifs.

# Construire le chemin vers le fichier JSON.
path = settings.corpus_path / "hopital_eval.json"

# Lire le fichier JSON.
#
# read_text() :
#     Lit le contenu du fichier comme du texte.
#
# json.loads() :
#     Convertit ce texte JSON en objets Python.
#
# Le résultat est une liste de dictionnaires.
questions = json.loads(
    path.read_text(encoding="utf-8")
)

# Sélectionner la question Q001.
#
# La boucle parcourt les questions jusqu'à trouver Q001.
#
# next() retourne le premier élément correspondant.
question = next(
    q for q in questions
    if q["id"] == "Q001"
)

# Afficher les informations de la question.
print("\n=== QUESTION ÉVALUÉE ===")

print("ID :", question["id"])
print("Type :", question["type"])
print("Question :", question["question"])
print("Réponse attendue :", question["answer"])

# [E09.3-B] Identifier les faits nécessaires à la réponse.
#
# Cette fonction lit les champs "grade" et "fact"
# de toutes les preuves de Q001.
facts = required_facts(question)

# Afficher les identifiants trouvés.
print("Faits nécessaires :", sorted(facts))

# Afficher leur nombre.
print("Nombre de faits nécessaires :", len(facts))

# ============================================================
# [E09.2 — SECTION 2] CHARGEMENT DE L'EXPÉRIENCE POSTGRESQL
# ============================================================

# Lire les résultats de l'expérience n° 1.
#
# Cette expérience correspond à notre première recherche
# dense utilisant BGE-M3.
#
# Les résultats ont déjà été enregistrés dans PostgreSQL.
result = get_results(1)

# Se connecter à Qdrant.
#
# Nous utiliserons cette connexion pour récupérer le texte
# des chunks retrouvés lors de l'expérience.
client = connect_qdrant()

# Créer une liste vide pour enregistrer les rangs des chunks
# contenant une preuve complète.
#
# Exemple attendu pour Q001 :
# evidence_ranks = [3]
evidence_ranks = []

# [E09.2-A] Créer une liste pour les grades de pertinence.
#
# Nous y enregistrerons un grade pour chaque chunk :
#
# 0 : aucune preuve reconnue ;
# 1 : information utile mais insuffisante ;
# 2 : preuve contenant la réponse ou un fait requis.
#
# Exemple attendu pour Q001 :
# retrieved_grades = [1, 0, 2, 0, 0]
retrieved_grades = []

# [E09.4-B2] Garder les preuves reconnues pour chaque chunk.
#
# La position dans cette liste correspond au rang Qdrant.
ranked_matches = []



# ============================================================
# [E09.2 — SECTION 3] VÉRIFICATION DES CHUNKS
# ============================================================

print("\n=== ANALYSE DES CHUNKS ===")

# result[5] contient les chunks enregistrés dans PostgreSQL.
#
# La boucle examine successivement chaque chunk.
#
# Pour Q001, cinq chunks ont été enregistrés.
for chunk in result[5]:

    # --------------------------------------------------------
    # [E09.2 — SECTION 3.1] RETROUVER LE CHUNK DANS QDRANT
    # --------------------------------------------------------

    # Reconstruire l'identifiant UUID du chunk.
    #
    # uuid5() produit un identifiant stable à partir
    # du chunk_id et de NAMESPACE_URL.
    #
    # str() convertit cet identifiant en chaîne de caractères.
    point_id = str(
        uuid5(NAMESPACE_URL, chunk["chunk_id"])
    )

    # Récupérer le point correspondant dans Qdrant.
    #
    # collection_name :
    #     Collection dans laquelle effectuer la recherche.
    #
    # ids :
    #     Liste des identifiants à récupérer.
    #
    # with_payload=True :
    #     Demander également les métadonnées du point.
    points = client.retrieve(
        collection_name=COLLECTION,
        ids=[point_id],
        with_payload=True,
    )

    # Vérifier que Qdrant a trouvé le point.
    #
    # Si aucun point n'est retourné, arrêter le script.
    # Cela évite de calculer les métriques avec des données
    # incomplètes.
    if not points:
        raise ValueError(
            f"Chunk introuvable dans Qdrant : {chunk['chunk_id']}"
        )

    # Récupérer le texte du chunk.
    #
    # points[0] :
    #     Premier point retourné.
    #
    # payload :
    #     Dictionnaire contenant les métadonnées du point.
    #
    # ["text"] :
    #     Texte original du chunk.
    text = points[0].payload["text"]

    # --------------------------------------------------------
    # [E09.2 — SECTION 3.2] ÉVALUER LES PREUVES
    # --------------------------------------------------------

    # Comparer le chunk aux preuves du golden dataset.
    #
    # judge_chunk() vérifie :
    # 1. Le nom du document.
    # 2. La présence de tous les extraits attendus.
    #
    # La fonction retourne les preuves correspondantes.
    matches = judge_chunk(
        question,
        chunk["document"],
        text,
    )
    # [E09.4-B3] Mémoriser les preuves reconnues pour ce chunk.
    ranked_matches.append(matches)

    # Déterminer le grade de pertinence.
    #
    # Une même question peut contenir plusieurs preuves.
    #
    # max() sélectionne le grade le plus élevé parmi
    # les preuves reconnues.
    #
    # default=0 signifie que si aucune preuve n'est reconnue,
    # le grade sera égal à zéro.
    grade = max(
        (evidence["grade"] for evidence in matches),
        default=0,
    )

    # --------------------------------------------------------
    # [E09.2-A] MÉMORISER LE GRADE DU CHUNK
    # --------------------------------------------------------

    # Ajouter le grade du chunk à la liste.
    #
    # IMPORTANT :
    # Cette instruction est à l'intérieur de la boucle for.
    #
    # Elle s'exécute donc une fois pour chaque chunk.
    #
    # Les grades sont conservés dans l'ordre de Qdrant.
    retrieved_grades.append(grade)

    # Pour Q001, la réponse attendue correspond à un seul fait.
    #
    # Nous considérons donc qu'un grade 2 indique une preuve
    # complète pour cette question.
    #
    # Cette règle sera adaptée ultérieurement pour les
    # questions qui nécessitent plusieurs faits distincts.
    has_evidence = grade == 2

    # Si la preuve complète est trouvée, mémoriser son rang.
    #
    # int() transforme le rang en entier.
    #
    # Exemple :
    # "3" devient 3.
    if has_evidence:
        evidence_ranks.append(
            int(chunk["rank"])
        )

    # --------------------------------------------------------
    # [E09.2 — SECTION 3.3] AFFICHER LE CHUNK
    # --------------------------------------------------------

    # Afficher les informations du chunk.
    print(
        f"\nRank: {chunk['rank']}"
        f"\nDocument: {chunk['document']}"
        f"\nChunk index: {chunk['chunk_index']}"
        f"\nEvidence grade: {grade}"
        f"\nComplete evidence: {has_evidence}"
    )

    # Afficher les 300 premiers caractères du texte.
    #
    # [:300] sélectionne les caractères de 0 à 299.
    #
    # Cela ne modifie pas le texte conservé dans Qdrant.
    print("Text:", text[:300])


# ============================================================
# [E09.2 — SECTION 4] CALCUL DES MÉTRIQUES
# ============================================================

print("\n=== CALCUL DES MÉTRIQUES ===")

# ------------------------------------------------------------
# [E09.2 — SECTION 4.1] PREMIÈRE PREUVE COMPLÈTE
# ------------------------------------------------------------

# Déterminer le premier rang contenant une preuve complète.
#
# Si evidence_ranks = [3], alors first_rank = 3.
#
# Si la liste est vide, first_rank = None.
# [E09.4-B4] Calculer la couverture des faits.
coverage = evaluate_fact_coverage(
    question,
    ranked_matches,
    k=5,
)

# Premier rang auquel tous les faits sont disponibles.
first_rank = coverage["first_complete_rank"]

print("Faits nécessaires :", sorted(coverage["required_facts"]))
print("Faits retrouvés :", sorted(coverage["found_facts"]))
print("Fact Recall@5 :", coverage["fact_recall"])


# ------------------------------------------------------------
# [E09.2 — SECTION 4.2] HIT@K ET RECIPROCAL RANK
# ------------------------------------------------------------

# Créer un dictionnaire contenant nos métriques.
#
# Hit@1 :
#     1 si la preuve complète est au rang 1.
#
# Hit@3 :
#     1 si la preuve complète apparaît parmi les 3 premiers.
#
# Hit@5 :
#     1 si la preuve complète apparaît parmi les 5 premiers.
#
# RR@5 :
#     Inverse du rang de la première preuve complète.
#
# Exemple :
#     Première preuve au rang 3.
#     RR@5 = 1 / 3 = 0.3333.
#
# float() convertit True en 1.0 et False en 0.0.
metrics = {

    "full_answer_hit@1": float(
        first_rank == 1
    ),

    "full_answer_hit@3": float(
        first_rank is not None
        and first_rank <= 3
    ),

    "full_answer_hit@5": float(
        first_rank is not None
        and first_rank <= 5
    ),

    "full_answer_rr@5": (
        1.0 / first_rank
        if first_rank and first_rank <= 5
        else 0.0
    ),
}

# [E09.4-B5] Ajouter la nouvelle métrique.
#
# La Section 5 enregistrera automatiquement cette métrique
# dans PostgreSQL avec les autres.
metrics["fact_recall@5"] = coverage["fact_recall"]

# ------------------------------------------------------------
# [E09.2-B] CALCUL DU nDCG@5
# ------------------------------------------------------------

# Le nDCG mesure la qualité de l'ordre des résultats.
#
# Contrairement à Hit@5, il tient compte :
# - du grade de pertinence ;
# - de la position du chunk dans le classement.
#
# Un chunk très pertinent situé au rang 1 contribue davantage
# qu'un chunk identique situé au rang 5.

# Lire les grades de référence du golden dataset.
#
# Chaque preuve contient le champ "grade".
#
# Pour Q001, les preuves de référence ont les grades :
# [2, 1].
#
# La fonction ndcg_at_k() les triera dans l'ordre idéal.
ideal_grades = [
    evidence["grade"]
    for evidence in question["evidence"]
]

# Calculer nDCG@5.
#
# retrieved_grades :
#     Grades réellement obtenus dans l'ordre de Qdrant.
#
# ideal_grades :
#     Grades des preuves fournies par le formateur.
#
# k=5 :
#     Évaluer les cinq premiers résultats.
#
# La fonction retourne un nombre entre 0 et 1.
metrics["ndcg@5"] = ndcg_at_k(
    retrieved_grades,
    ideal_grades,
    k=5,
)

# Afficher les grades utilisés pour comprendre le calcul.
print("Grades récupérés :", retrieved_grades)
print("Grades de référence :", ideal_grades)

# Afficher la nouvelle métrique.
print(
    "nDCG@5 calculé :",
    round(metrics["ndcg@5"], 4)
)


# ============================================================
# [E09.2 — SECTION 5] ENREGISTREMENT DANS POSTGRESQL
# ============================================================

# À ce stade, toutes les métriques sont calculées.
#
# Nous pouvons donc les enregistrer dans PostgreSQL.
#
# La table scores existe déjà.
#
# Chaque ligne contient :
# - experiment_id ;
# - question_id ;
# - question_type ;
# - metric ;
# - value ;
# - reason.

# Ouvrir une connexion PostgreSQL.
#
# Le bloc with assure la gestion de la transaction.
#
# Si toutes les instructions réussissent, les modifications
# sont validées.
with psycopg.connect(settings.postgres_url) as conn:

    # Parcourir le dictionnaire des métriques.
    #
    # items() retourne successivement :
    # - metric : le nom de la métrique ;
    # - value  : sa valeur.
    for metric, value in metrics.items():

        # Exécuter une requête SQL.
        #
        # INSERT INTO :
        #     Ajouter une ligne dans la table.
        #
        # VALUES (%s, ...) :
        #     Emplacements pour les valeurs transmises à psycopg.
        #
        # ON CONFLICT :
        #     Détecter une métrique déjà enregistrée.
        #
        # DO UPDATE :
        #     Mettre à jour la métrique existante plutôt
        #     que créer un doublon.
        conn.execute(
            """
            INSERT INTO scores (
                experiment_id,
                question_id,
                question_type,
                metric,
                value,
                reason
            )

            VALUES (%s, %s, %s, %s, %s, %s)

            ON CONFLICT (
                experiment_id,
                question_id,
                metric
            )

            DO UPDATE SET
                value = EXCLUDED.value,
                reason = EXCLUDED.reason
            """,
            (
                1,                  # ID de l'expérience
                question["id"],     # Q001
                question["type"],   # table
                metric,             # Nom de la métrique
                value,              # Valeur calculée
                (
                    f"Evidence ranks: {evidence_ranks}; "
                    f"retrieved grades: {retrieved_grades}"
                ),
            ),
        )


# ============================================================
# [E09.2 — SECTION 6] AFFICHAGE DES MÉTRIQUES ENREGISTRÉES
# ============================================================

print("\n=== MÉTRIQUES ENREGISTRÉES DANS POSTGRESQL ===")

# Afficher chaque métrique.
#
# Le dictionnaire contient maintenant cinq métriques :
# - full_answer_hit@1 ;
# - full_answer_hit@3 ;
# - full_answer_hit@5 ;
# - full_answer_rr@5 ;
# - ndcg@5.
for metric, value in metrics.items():

    # round(value, 4) limite l'affichage à quatre décimales.
    print(
        metric,
        round(value, 4)
    )

print("\nÉvaluation Q001 terminée.")