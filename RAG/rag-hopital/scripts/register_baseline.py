import hashlib
import json
from pathlib import Path

from rag_hopital.etl.index import COLLECTION, connect_qdrant
from rag_hopital.etl.log_etl import start_run, finish_run


source = Path("data/chunks/chunks.jsonl")

records = [
    json.loads(line)
    for line in source.read_text(encoding="utf-8").splitlines()
]

documents = {record["document"] for record in records}

client = connect_qdrant()
points = client.count(COLLECTION, exact=True).count

assert len(documents) == 280
assert len(records) == 1173
assert points == 1173

baseline = {
    "version": "baseline_v1",
    "documents": len(documents),
    "chunks": len(records),
    "chunk_size_limit": 512,
    "max_tokens_observed": 371,
    "embedding_model": "bge-m3",
    "vector_dimensions": 1024,
    "qdrant_collection": COLLECTION,
    "qdrant_points": points,
    "chunks_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "validation": "counts_verified; point identities not yet checked",
}

run_id = start_run(
    stage="baseline_snapshot",
    configuration={"version": "baseline_v1"},
)

finish_run(
    run_id,
    status="success",
    summary=baseline,
)

print(json.dumps(baseline, indent=2))
print("PostgreSQL Run ID:", run_id)