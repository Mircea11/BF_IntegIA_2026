"""
[E10 / E11] Exécuter et évaluer une expérience RAG définie en TOML.

Depuis le répertoire racine de rag-hopital :
    PYTHONPATH=src .venv/bin/python scripts/run_experiment.py experiments/hybrid_bge_bm25_rerank.toml --check-config
    PYTHONPATH=src .venv/bin/python scripts/run_experiment.py experiments/hybrid_bge_bm25_rerank.toml --limit 3
    PYTHONPATH=src .venv/bin/python scripts/run_experiment.py --evaluate-existing 6

--check-config : valide sans écrire dans PostgreSQL ni lancer de modèle.
--limit N      : crée une nouvelle expérience sur N questions.
--evaluate-existing : évalue les résultats d'une expérience enregistrée.
"""

# ============================================================
# SECTION 0 — IMPORTS
# ============================================================

import argparse
import json
import tomllib
from pathlib import Path
from time import perf_counter

from rag_hopital.config import settings
from rag_hopital.db import create_experiment, finish_experiment, save_question_result
from rag_hopital.etl.index import COLLECTION, HYBRID_COLLECTION
from rag_hopital.evaluation.runner import evaluate_saved_experiment
from rag_hopital.rag.search import search


# ============================================================
# SECTION 1 — LIRE ET VALIDER LE TOML
# ============================================================

def load_and_validate_config(path: Path) -> dict:
    """Lire le TOML et vérifier les options réellement prises en charge."""

    if not path.is_file():
        raise FileNotFoundError(f"Fichier TOML introuvable : {path}")

    with path.open("rb") as file:
        config = tomllib.load(file)

    search_config = config.get("search", {})
    chunk_config = config.get("chunking", {})
    embedder_config = config.get("embedder", {})

    method = search_config.get("method")
    if method not in {"dense", "sparse", "hybrid"}:
        raise ValueError(f"Méthode non prise en charge : {method}")

    if not config.get("name"):
        raise ValueError("Le TOML doit définir 'name'.")

    if config.get("dataset") != "hopital_eval.json":
        raise ValueError("Seul hopital_eval.json est pris en charge actuellement.")

    # Les collections existantes ont déjà été indexées avec ces paramètres.
    if (
        chunk_config.get("max_tokens") != 512
        or chunk_config.get("patient_line") is not True
        or chunk_config.get("overlap") != 0
    ):
        raise ValueError("Index actuel : chunks de 512 tokens, ligne patient, overlap=0.")

    if embedder_config.get("model") != "bge-m3":
        raise NotImplementedError("Autre embedder : nouvelle collection requise.")

    # Les métriques de retrieval sont actuellement calculées à k=5.
    if search_config.get("top_k") != 5:
        raise NotImplementedError("L'évaluation actuelle utilise top_k=5.")

    candidates = search_config.get("candidates", 30)
    if type(candidates) is not int or candidates < 5:
        raise ValueError("'candidates' doit être un entier >= 5.")

    expected_collection = COLLECTION if method == "dense" else HYBRID_COLLECTION
    if search_config.get("collection") != expected_collection:
        raise ValueError(
            f"Collection incompatible avec {method} : attendue {expected_collection}"
        )

    if method in {"sparse", "hybrid"}:
        if (
            search_config.get("sparse_model") != "Qdrant/bm25"
            or search_config.get("sparse_language") != "french"
        ):
            raise NotImplementedError("Sparse pris en charge : Qdrant/bm25, français.")

    if method == "hybrid" and search_config.get("fusion") != "rrf":
        raise NotImplementedError("Fusion implémentée actuellement : rrf.")

    # E11 — Le reranker est optionnel et réservé à Hybrid.
    reranker_config = config.get("reranker", {})
    rerank_enabled = reranker_config.get("enabled")

    if not isinstance(rerank_enabled, bool):
        raise ValueError("reranker.enabled doit être true ou false.")

    if rerank_enabled:
        if method != "hybrid":
            raise ValueError("E11 : le reranking nécessite method='hybrid'.")
        if reranker_config.get("model") != "BAAI/bge-reranker-v2-m3":
            raise ValueError("E11 : modèle de reranking non pris en charge.")
        if reranker_config.get("device") != "cpu":
            raise ValueError("E11 : seul device='cpu' est pris en charge.")

    # La génération LLM n'est pas encore intégrée à ce script.
    if config.get("generation", {}).get("enabled") is not False:
        raise NotImplementedError("La génération LLM n'est pas encore implémentée.")

    return config


# ============================================================
# SECTION 2 — SÉLECTIONNER LES QUESTIONS
# ============================================================

def load_questions(limit: int | None) -> list[dict]:
    """Charger les 100 questions du golden dataset, puis appliquer --limit."""

    path = settings.corpus_path / "hopital_eval.json"
    questions = json.loads(path.read_text(encoding="utf-8"))

    # Les questions hors corpus seront traitées lors de l'étape génération LLM.
    grounded = [q for q in questions if q["type"] != "out_of_corpus"]

    if len(grounded) != 100:
        raise ValueError(f"100 questions attendues ; trouvé : {len(grounded)}")

    return grounded[:limit] if limit is not None else grounded


# ============================================================
# SECTION 3 — EXÉCUTER UNE EXPÉRIENCE
# ============================================================

def run_retrieval(config: dict, questions: list[dict], source: Path) -> None:
    """Créer une expérience, chercher les chunks et enregistrer les résultats."""

    search_config = config["search"]
    method = search_config["method"]
    top_k = search_config["top_k"]
    candidates = search_config.get("candidates", 30)
    rerank_enabled = config["reranker"]["enabled"]  # E11

    # Conserver les paramètres exacts et la liste des questions de l'expérience.
    recorded_config = {
        **config,
        "configuration_file": str(source),
        "question_ids": [q["id"] for q in questions],
        "question_count": len(questions),
        "evaluation": "retrieval_only",
    }

    experiment_start = perf_counter()
    experiment_id = create_experiment(recorded_config)
    print(f"\nExpérience créée : {experiment_id}", flush=True)

    for question in questions:
        start = perf_counter()

        # E11 : rerank=True seulement si [reranker] enabled=true dans le TOML.
        points = search(
            question["question"],
            top_k=top_k,
            method=method,
            candidates=candidates,
            rerank=rerank_enabled,
        )

        latency_ms = (perf_counter() - start) * 1000

        save_question_result(
            experiment_id=experiment_id,
            question=question,
            points=points,
            latency_ms=latency_ms,
        )

        print(
            f"{question['id']} | {method} | rerank={rerank_enabled} | "
            f"{len(points)} chunks | {latency_ms:.2f} ms",
            flush=True,
        )

    duration_s = perf_counter() - experiment_start
    finish_experiment(experiment_id, duration_s)

    print(
        f"\nTerminé | experiment_id={experiment_id} | "
        f"questions={len(questions)} | durée={duration_s:.2f}s",
        flush=True,
    )
    print(f"Pour évaluer : --evaluate-existing {experiment_id}")


# ============================================================
# SECTION 4 — INTERFACE DU TERMINAL
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Expériences RAG configurées par TOML")
    parser.add_argument("config_file", nargs="?", type=Path)
    parser.add_argument("--limit", type=int, help="Nombre de questions à tester")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Vérifier le TOML sans écrire dans PostgreSQL",
    )
    parser.add_argument(
        "--evaluate-existing",
        type=int,
        metavar="ID",
        help="Évaluer une expérience PostgreSQL déjà enregistrée",
    )
    args = parser.parse_args()

    if args.evaluate_existing is not None:
        if args.config_file or args.limit is not None or args.check_config:
            parser.error("--evaluate-existing ne se combine pas avec les autres options")
        evaluate_saved_experiment(args.evaluate_existing)
        return

    if args.config_file is None:
        parser.error("Indiquer un fichier TOML ou --evaluate-existing ID")

    if args.limit is not None and args.limit < 1:
        parser.error("--limit doit être >= 1")

    config = load_and_validate_config(args.config_file)
    questions = load_questions(args.limit)

    print(
        f"Configuration OK : {config['name']} | "
        f"method={config['search']['method']} | "
        f"rerank={config['reranker']['enabled']} | "
        f"top_k={config['search']['top_k']} | "
        f"candidates={config['search'].get('candidates', 30)} | "
        f"questions={len(questions)}",
        flush=True,
    )

    if args.check_config:
        print("Vérification seule : aucune expérience créée.")
        return

    run_retrieval(config, questions, args.config_file)


if __name__ == "__main__":
    main()