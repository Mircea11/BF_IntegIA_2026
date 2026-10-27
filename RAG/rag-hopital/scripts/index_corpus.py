import argparse
import json
from pathlib import Path

from rag_hopital.config import settings
from rag_hopital.etl.index import (
    COLLECTION,
    connect_qdrant,
    index_batch,
)
from rag_hopital.etl.log_etl import (
    start_run,
    log_event,
    finish_run,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    source = Path("data/chunks/chunks.jsonl")

    run_id = start_run(
        stage="qdrant_indexing",
        configuration={
            "collection": COLLECTION,
            "embedding_model": settings.embedder_path,
            "vector_dimensions": 1024,
            "batch_size": 16,
            "limit": args.limit,
        },
    )

    processed = 0
    selected = 0

    try:
        client = connect_qdrant()
        batch = []

        with source.open(encoding="utf-8") as file:
            for line in file:
                if args.limit is not None and selected >= args.limit:
                    break

                batch.append(json.loads(line))
                selected += 1

                if len(batch) == 16:
                    index_batch(client, batch)
                    processed += len(batch)

                    log_event(
                        run_id,
                        step="index_batch",
                        status="success",
                        input_count=len(batch),
                        output_count=len(batch),
                    )

                    batch.clear()
                    print(f"Indexed: {processed}", flush=True)

            if batch:
                index_batch(client, batch)
                processed += len(batch)

                log_event(
                    run_id,
                    step="index_batch",
                    status="success",
                    input_count=len(batch),
                    output_count=len(batch),
                )

        points = client.count(COLLECTION, exact=True).count

        finish_run(
            run_id,
            status="success",
            summary={
                "processed": processed,
                "qdrant_points": points,
            },
        )

        print("Processed:", processed)
        print("Collection:", COLLECTION)
        print("Qdrant points:", points)
        print("ETL Run ID:", run_id)

    except Exception as error:
        finish_run(
            run_id,
            status="failed",
            summary={"processed": processed},
            error_message=str(error),
        )
        raise


if __name__ == "__main__":
    main()