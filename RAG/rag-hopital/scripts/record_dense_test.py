import json
from time import perf_counter

from rag_hopital.config import settings
from rag_hopital.db import (
    init_db,
    save_retrieval_run,
    get_results,
)
from rag_hopital.etl.index import COLLECTION
from rag_hopital.rag.search import search


# Load the instructor's evaluation dataset
path = settings.corpus_path / "hopital_eval.json"
questions = json.loads(path.read_text(encoding="utf-8"))

# First reference question
question = next(q for q in questions if q["id"] == "Q001")

# Execute retrieval and measure latency
start = perf_counter()
points = search(question["question"], top_k=5)
latency_ms = (perf_counter() - start) * 1000

# Configuration of this experiment
config = {
    "name": "dense_Q001_test",
    "dataset": "hopital_eval.json",
    "method": "dense",
    "embedding_model": "bge-m3",
    "collection": COLLECTION,
    "top_k": 5,
    "reranker": None,
    "generation": None,
}

# Initialize and save
init_db()

experiment_id = save_retrieval_run(
    question,
    points,
    latency_ms,
    config,
)

# Read the saved results back from PostgreSQL
result = get_results(experiment_id)

print("Experiment ID:", experiment_id)
print("Experiment:", result[0])
print("Question ID:", result[1])
print("Question:", result[2])
print("Expected answer:", result[3])
print("Latency (ms):", round(result[4], 2))

print("\nRetrieved chunks:")
for chunk in result[5]:
    print(
        chunk["rank"],
        chunk["document"],
        round(chunk["score"], 4),
    )