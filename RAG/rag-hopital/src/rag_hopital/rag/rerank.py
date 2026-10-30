"""
E11 — Reranking des résultats RAG.

Entrée :
    Question + candidats récupérés dans Qdrant.

Traitement :
    BGE Reranker v2 M3 (Cross-Encoder).

Sortie :
    Top K des chunks, classés selon leur pertinence.

Exécution locale sur CPU, sans téléchargement.
"""

from functools import lru_cache

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


# ============================================================
# E11-A — CONFIGURATION
# ============================================================

MODEL_PATH = "/home/bm/models/rag/reranker/bge-reranker-v2-m3"

MAX_LENGTH = 512


# ============================================================
# E11-B — CHARGEMENT DU MODÈLE
# ============================================================

@lru_cache(maxsize=1)
def load_reranker():
    """Charger le modèle une seule fois et le conserver en mémoire."""

    torch.set_num_threads(2)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
    ).to("cpu")

    model.eval()

    return tokenizer, model


# ============================================================
# E11-C — RERANKING
# ============================================================

def rerank_points(question: str, points: list, top_k: int = 5) -> list:
    """
    Reclasser les candidats Qdrant selon leur pertinence.

    question : question de l'utilisateur.
    points   : résultats provenant de Qdrant.
    top_k    : nombre de chunks à conserver.
    """

    if not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    if top_k < 1:
        raise ValueError("top_k doit être >= 1.")

    if not points:
        return []

    # 1. Extraire les textes des chunks.
    documents = [
        (point.payload or {}).get("text")
        for point in points
    ]

    if any(not isinstance(text, str) or not text.strip()
           for text in documents):
        raise ValueError("Un candidat ne contient pas de texte valide.")

    # 2. Charger le modèle local.
    tokenizer, model = load_reranker()

    # 3. Construire les paires question-document.
    pairs = [
        [question, document]
        for document in documents
    ]

    # 4. Convertir les textes en tokens.
    inputs = tokenizer(
        pairs,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    # 5. Calculer les scores de pertinence.
    with torch.inference_mode():
        scores = model(**inputs).logits.view(-1).tolist()

    # 6. Classer les candidats par score décroissant.
    ranked = sorted(
        zip(points, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    # 7. Préparer les meilleurs candidats.
    results = []

    for point, score in ranked[:top_k]:

        payload = dict(point.payload or {})

        # Conserver le score de recherche initial.
        payload["retrieval_score"] = float(point.score)

        # Enregistrer le nouveau score de reranking.
        payload["reranker_score"] = float(score)

        # Créer une copie : ne pas modifier le point original.
        reranked_point = point.model_copy(
            update={
                "score": float(score),
                "payload": payload,
            }
        )

        results.append(reranked_point)

    return results