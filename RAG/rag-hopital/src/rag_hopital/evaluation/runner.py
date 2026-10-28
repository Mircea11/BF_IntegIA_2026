"""
E09.5-D2 / E09.5-G — Évaluation d'une expérience RAG enregistrée.

Lit les résultats déjà enregistrés dans PostgreSQL, récupère le texte
correspondant dans Qdrant, calcule les métriques et les enregistre.
Aucune nouvelle recherche dense et aucune nouvelle expérience n'est créée.
"""

# ============================================================
# [E09.5-D2-B — SECTION 0] IMPORTS
# ============================================================

import json
from uuid import NAMESPACE_URL, uuid5

from rag_hopital.config import settings
from rag_hopital.db import get_experiment_questions, save_question_scores
from rag_hopital.etl.index import COLLECTION, connect_qdrant
from rag_hopital.evaluation.metrics import (
    evaluate_fact_coverage,
    judge_chunk,
    ndcg_at_k,
)


# ============================================================
# [E09.5-D2-B — SECTION 1] ÉVALUER UNE EXPÉRIENCE EXISTANTE
# ============================================================

def evaluate_saved_experiment(experiment_id: int) -> None:
    """Évaluer les questions de l'expérience et sauvegarder six scores par question."""

    # --------------------------------------------------------
    # [D2-B1] CHARGER LES QUESTIONS DE RÉFÉRENCE
    # --------------------------------------------------------

    # Le fichier du formateur contient 106 questions, dont six out_of_corpus.
    path = settings.corpus_path / "hopital_eval.json"
    questions = json.loads(path.read_text(encoding="utf-8"))

    # Associer chaque identifiant à sa question complète : Q001 -> dictionnaire.
    question_by_id = {question["id"]: question for question in questions}

    # --------------------------------------------------------
    # [D2-B2] LIRE L'EXPÉRIENCE DEPUIS POSTGRESQL
    # --------------------------------------------------------

    # Chaque ligne contient l'identifiant de question et cinq chunks classés.
    saved_questions = get_experiment_questions(experiment_id)

    if not saved_questions:
        raise ValueError(f"No saved questions for experiment {experiment_id}")

    # Une connexion Qdrant suffit pour toute l'évaluation.
    client = connect_qdrant()

    print("\n=== EVALUATION STARTED ===")
    print("Experiment ID:", experiment_id)
    print("Questions:", len(saved_questions))

    # --------------------------------------------------------
    # [D2-B3] TRAITER CHAQUE QUESTION
    # --------------------------------------------------------

    for question_id, chunks in saved_questions:
        if question_id not in question_by_id:
            raise ValueError(f"Unknown question ID: {question_id}")

        question = question_by_id[question_id]

        # Les questions sans réponse dans le corpus seront évaluées séparément.
        if question["type"] == "out_of_corpus":
            raise ValueError(
                f"{question_id}: refusal evaluation is not implemented"
            )

        # Respecter l'ordre de pertinence enregistré lors de la recherche.
        ranked_chunks = sorted(chunks, key=lambda chunk: int(chunk["rank"]))

        # Liste des grades utilisée pour calculer nDCG@5.
        retrieved_grades = []

        # Liste des preuves par rang utilisée pour la couverture des faits.
        ranked_matches = []

        # ----------------------------------------------------
        # [E09.5-G1] PRÉPARER LE COMPTAGE DES PREUVES UNIQUES
        # ----------------------------------------------------

        # Une preuve de référence ne doit contribuer qu'une fois au nDCG.
        # Les entiers 0, 1, 2... sont les positions des preuves de référence.
        seen_evidence = set()

        # judge_chunk() renvoie les mêmes dictionnaires que question["evidence"].
        # id() permet de retrouver précisément leur position, même si deux
        # dictionnaires ont des contenus similaires.
        evidence_index_by_id = {
            id(evidence): index
            for index, evidence in enumerate(question["evidence"])
        }

        # ----------------------------------------------------
        # [D2-B4] ANALYSER LES CHUNKS DE LA QUESTION
        # ----------------------------------------------------

        for chunk in ranked_chunks:
            chunk_id = chunk["chunk_id"]

            # Reconstituer l'UUID stable utilisé dans Qdrant à l'indexation.
            point_id = str(uuid5(NAMESPACE_URL, chunk_id))

            # Retrouver le texte du chunk SANS lancer de recherche vectorielle.
            points = client.retrieve(
                collection_name=COLLECTION,
                ids=[point_id],
                with_payload=True,
            )

            if not points:
                raise ValueError(f"Missing Qdrant chunk: {chunk_id}")

            text = points[0].payload["text"]

            # Identifier les preuves de référence présentes dans ce chunk.
            matches = judge_chunk(question, chunk["document"], text)

            # Conserver TOUTES les correspondances pour calculer le Fact Recall.
            # Le dédoublonnage n'affecte PAS cette métrique.
            ranked_matches.append(matches)

            # ------------------------------------------------
            # [E09.5-G2] GRADE DES PREUVES NOUVELLES UNIQUEMENT
            # ------------------------------------------------

            new_grades = []

            for evidence in matches:
                # Identifier la preuve dans la liste de référence.
                reference_index = evidence_index_by_id[id(evidence)]

                if reference_index not in seen_evidence:
                    # Marquer cette preuve comme déjà comptée.
                    seen_evidence.add(reference_index)

                    # Ajouter son grade seulement à sa première apparition.
                    new_grades.append(evidence["grade"])

            # Cette ligne est DANS la boucle des chunks, mais HORS de la
            # boucle des preuves : un grade par chunk, jamais par preuve.
            grade = max(new_grades, default=0)
            retrieved_grades.append(grade)

        # ----------------------------------------------------
        # [D2-B5] CALCULER LA COUVERTURE DES FAITS
        # ----------------------------------------------------

        # La couverture des faits considère toutes les correspondances.
        coverage = evaluate_fact_coverage(question, ranked_matches, k=5)
        first_rank = coverage["first_complete_rank"]

        # ----------------------------------------------------
        # [D2-B6] CALCULER LES SIX MÉTRIQUES
        # ----------------------------------------------------

        metrics = {
            "full_answer_hit@1": float(first_rank == 1),
            "full_answer_hit@3": float(
                first_rank is not None and first_rank <= 3
            ),
            "full_answer_hit@5": float(
                first_rank is not None and first_rank <= 5
            ),
            "full_answer_rr@5": (
                1.0 / first_rank
                if first_rank is not None and first_rank <= 5
                else 0.0
            ),
            "fact_recall@5": coverage["fact_recall"],
        }

        # Le nDCG utilise ici UNE fois chaque preuve de référence.
        # C'est notre convention "preuves uniques", à documenter avant
        # une comparaison externe avec un nDCG classique par chunk.
        ideal_grades = [
            evidence["grade"] for evidence in question["evidence"]
        ]

        metrics["ndcg@5"] = ndcg_at_k(
            retrieved_grades,
            ideal_grades,
            k=5,
        )

        # Vérification : une normalisation correcte ne dépasse jamais 1.
        if not 0.0 <= metrics["ndcg@5"] <= 1.000001:
            raise ValueError(
                f"Invalid nDCG for {question_id}: {metrics['ndcg@5']}"
            )

        # ----------------------------------------------------
        # [D2-B7] ENREGISTRER LES SCORES DANS POSTGRESQL
        # ----------------------------------------------------

        reason = (
            "nDCG: unique reference evidence; "
            f"Grades: {retrieved_grades}; "
            f"Required facts: {sorted(coverage['required_facts'])}; "
            f"Found facts: {sorted(coverage['found_facts'])}; "
            f"First complete rank: {first_rank}"
        )

        # ON CONFLICT dans save_question_scores() évite les doublons.
        save_question_scores(
            experiment_id=experiment_id,
            question=question,
            metrics=metrics,
            reason=reason,
        )

        # ----------------------------------------------------
        # [D2-B8] AFFICHER UN BILAN POUR CETTE QUESTION
        # ----------------------------------------------------

        print(
            f"\n{question_id} ({question['type']})"
            f"\n  Grades: {retrieved_grades}"
            f"\n  Fact recall@5: {metrics['fact_recall@5']:.4f}"
            f"\n  Full-answer hit@5: {metrics['full_answer_hit@5']:.4f}"
            f"\n  nDCG@5: {metrics['ndcg@5']:.4f}"
        )

    # --------------------------------------------------------
    # [D2-B9] CONFIRMER LA FIN DU TRAITEMENT
    # --------------------------------------------------------

    print("\n=== EVALUATION COMPLETED ===")
    print("Experiment ID:", experiment_id)
    print("Questions evaluated:", len(saved_questions))
    print("Scores saved in PostgreSQL.")