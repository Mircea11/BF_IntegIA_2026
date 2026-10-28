"""
[E10-D2] Exécuter une expérience RAG à partir d'un fichier TOML.

Exemples (depuis ~/formation/RAG/rag-hopital) :
    uv run python scripts/run_experiment.py experiments/sparse_bm25.toml --check-config
    uv run python scripts/run_experiment.py experiments/sparse_bm25.toml --limit 3
    uv run python scripts/run_experiment.py --evaluate-existing 3

Une exécution normale crée UNE nouvelle expérience PostgreSQL.
--check-config vérifie les paramètres SANS créer d'expérience.
--evaluate-existing réévalue des résultats déjà enregistrés.
"""

# ============================================================
# [E10-D2 — SECTION 0] IMPORTS
# ============================================================

import argparse  # Lire les options transmises dans le terminal.
import json  # Lire les questions du golden dataset.
import tomllib  # Lire les fichiers TOML (inclus dans Python 3.11+).
from pathlib import Path  # Manipuler les chemins de fichiers.
from time import perf_counter  # Mesurer la durée des recherches.

from rag_hopital.config import settings
from rag_hopital.db import (
    create_experiment,
    finish_experiment,
    save_question_result,
)
from rag_hopital.etl.index import COLLECTION, HYBRID_COLLECTION
from rag_hopital.evaluation.runner import evaluate_saved_experiment
from rag_hopital.rag.search import search


# ============================================================
# [E10-D2 — SECTION 1] LIRE ET VALIDER LE TOML
# ============================================================

def load_and_validate_config(path: Path) -> dict:
    """Lire le TOML et refuser toute option pas encore implémentée."""

    # Le chemin est relatif au dossier où l'on lance la commande.
    if not path.is_file():
        raise FileNotFoundError(f"Fichier TOML introuvable : {path}")

    # tomllib.load() transforme le TOML en dictionnaire Python.
    with path.open("rb") as file:
        config = tomllib.load(file)

    # Les sections du TOML sont elles-mêmes des dictionnaires.
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

    # Les collections sont déjà indexées avec ces paramètres.
    # Changer le chunking ou l'embedder exige une autre collection.
    if (
        chunk_config.get("max_tokens") != 512
        or chunk_config.get("patient_line") is not True
        or chunk_config.get("overlap") != 0
    ):
        raise ValueError("Index actuel : chunks de 512 tokens, ligne patient, overlap=0.")

    if embedder_config.get("model") != "bge-m3":
        raise NotImplementedError("Autre embedder : nouvelle collection requise.")

    # L'évaluateur actuel calcule les métriques à k=5.
    if search_config.get("top_k") != 5:
        raise NotImplementedError("L'évaluation actuelle utilise top_k=5.")

    candidates = search_config.get("candidates", 30)
    if not isinstance(candidates, int) or candidates < 5:
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

    # Ces modules seront ajoutés lors des étapes suivantes.
    # On refuse de prétendre les avoir utilisés avant leur implémentation.
    if config.get("reranker", {}).get("enabled") is not False:
        raise NotImplementedError("Le reranker n'est pas encore implémenté.")

    if config.get("generation", {}).get("enabled") is not False:
        raise NotImplementedError("La génération LLM n'est pas encore implémentée.")

    return config


# ============================================================
# [E10-D2 — SECTION 2] SÉLECTIONNER LES QUESTIONS
# ============================================================

def load_questions(limit: int | None) -> list[dict]:
    """Charger les 100 questions avec preuves ; --limit en conserve N."""

    path = settings.corpus_path / "hopital_eval.json"
    questions = json.loads(path.read_text(encoding="utf-8"))

    # Les six questions out_of_corpus seront évaluées avec le LLM.
    grounded = [q for q in questions if q["type"] != "out_of_corpus"]

    if len(grounded) != 100:
        raise ValueError(f"100 questions attendues ; trouvé : {len(grounded)}")

    # [:limit] permet de tester trois questions sans exécuter les 100.
    return grounded[:limit] if limit is not None else grounded


# ============================================================
# [E10-D2 — SECTION 3] EXÉCUTER LES RECHERCHES
# ============================================================

def run_retrieval(config: dict, questions: list[dict], source: Path) -> None:
    """Créer une expérience, rechercher, enregistrer puis terminer."""

    search_config = config["search"]
    method = search_config["method"]
    top_k = search_config["top_k"]
    candidates = search_config.get("candidates", 30)

    # Copie indépendante : les résultats sont associés aux paramètres
    # exacts du TOML et aux questions réellement sélectionnées.
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

    # Toutes les questions partagent le même experiment_id.
    for question in questions:
        start = perf_counter()

        # Les options du TOML pilotent la fonction search().
        points = search(
            question["question"],
            top_k=top_k,
            method=method,
            candidates=candidates,
        )

        latency_ms = (perf_counter() - start) * 1000

        save_question_result(
            experiment_id=experiment_id,
            question=question,
            points=points,
            latency_ms=latency_ms,
        )

        print(
            f"{question['id']} | {method} | "
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
# [E10-D2 — SECTION 4] INTERFACE DU TERMINAL
# ============================================================

def main() -> None:
    """Choisir entre vérifier, lancer ou réévaluer une expérience."""

    parser = argparse.ArgumentParser(description="Expériences RAG configurées par TOML")
    parser.add_argument("config_file", nargs="?", type=Path)
    parser.add_argument("--limit", type=int, help="Nombre de questions à tester")
    parser.add_argument(
        "--check-config", action="store_true",
        help="Vérifier le TOML sans écrire dans PostgreSQL",
    )
    parser.add_argument(
        "--evaluate-existing", type=int, metavar="ID",
        help="Évaluer une expérience PostgreSQL déjà enregistrée",
    )
    args = parser.parse_args()

    # Mode réévaluation : ne pas créer une nouvelle expérience.
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
