import json
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from rag_hopital.config import settings


COLLECTION = "hopital_bge_m3_512"
VECTOR_SIZE = 1024


def embed_texts(texts):
    """Generate embeddings using the local BGE-M3 server."""

    payload = {
        "model": settings.embedder_path,
        "input": texts,
    }

    request = Request(
        f"{settings.embeddings_url}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urlopen(request, timeout=120) as response:
        result = json.load(response)

    data = sorted(result["data"], key=lambda item: item["index"])
    vectors = [item["embedding"] for item in data]

    if len(vectors) != len(texts):
        raise ValueError("Embedding count mismatch")

    if any(len(vector) != VECTOR_SIZE for vector in vectors):
        raise ValueError("Unexpected embedding dimensions")

    return vectors


def connect_qdrant():
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )

    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

    return client


def index_batch(client, records):
    vectors = embed_texts([record["text"] for record in records])

    points = [
        models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, record["chunk_id"])),
            vector=vector,
            payload=record,
        )
        for record, vector in zip(records, vectors)
    ]

    client.upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True,
    )
# ============================================================
# [E10-B2] HYBRID COLLECTION — DENSE + SPARSE
# ============================================================

# Separate collection for hybrid retrieval experiments.
#
# The original dense collection remains unchanged.
HYBRID_COLLECTION = "hopital_bge_m3_512_hybrid"


def connect_hybrid_qdrant():
    """
    Connect to Qdrant and prepare the hybrid collection.

    The collection contains:
    - dense : 1024-dimensional BGE-M3 vectors;
    - bm25  : sparse vectors for lexical search.

    An existing collection is never deleted.
    """

    # [E10-B2.1] Reuse our existing Qdrant connection.
    client = connect_qdrant()

    # [E10-B2.2] Create the collection only if absent.
    if not client.collection_exists(HYBRID_COLLECTION):

        client.create_collection(
            collection_name=HYBRID_COLLECTION,

            # Dense vector configuration.
            vectors_config={
                "dense": models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            },

            # Sparse vector configuration.
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                ),
            },
        )

    # [E10-B2.3] Return the Qdrant client.
    return client
# ============================================================
# [E10-B3] REUSE DENSE VECTORS AND ADD BM25
# ============================================================

def copy_dense_to_hybrid(
    max_points: int | None = None,
    batch_size: int = 16,
) -> int:
    """
    Copy existing dense vectors into the hybrid collection.

    Generate only the missing BM25 sparse vectors.

    max_points:
        Maximum number of points to process.
        None means the complete collection.

    batch_size:
        Number of points processed together.

    Returns:
        Number of points processed.
    """

    # [E10-B3.1] Import our existing sparse embedding tool.
    from fastembed import SparseTextEmbedding

    # Use only the BM25 resources already cached locally.
    # local_files_only=True prevents model downloads.
    bm25 = SparseTextEmbedding(
        model_name="Qdrant/bm25",
        language="french",
        local_files_only=True,
    )

    # [E10-B3.2] Connect to Qdrant.
    client = connect_hybrid_qdrant()

    # offset identifies where the next page starts.
    offset = None

    # Count the points processed.
    copied = 0

    # [E10-B3.3] Read the source collection in batches.
    while True:

        # Determine how many points to read.
        page_size = batch_size

        if max_points is not None:
            remaining = max_points - copied

            if remaining <= 0:
                break

            page_size = min(batch_size, remaining)

        # Retrieve stored text, metadata and dense vectors.
        records, next_offset = client.scroll(
            collection_name=COLLECTION,
            limit=page_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        # Stop when the collection has no more records.
        if not records:
            break

        # [E10-B3.4] Obtain the existing chunk texts.
        texts = [
            record.payload["text"]
            for record in records
        ]

        # Generate BM25 vectors for these texts.
        sparse_vectors = list(bm25.embed(texts))

        # Prepare the points for the hybrid collection.
        points = []

        for record, sparse in zip(records, sparse_vectors):

            # Our original collection uses unnamed dense vectors.
            dense_vector = record.vector

            # Validate the retrieved vector before copying.
            if (
                not isinstance(dense_vector, list)
                or len(dense_vector) != VECTOR_SIZE
            ):
                raise ValueError(
                    f"Invalid dense vector for point {record.id}"
                )

            # Build a point containing both vector types.
            point = models.PointStruct(
                id=record.id,

                vector={
                    "dense": dense_vector,

                    "bm25": models.SparseVector(
                        indices=sparse.indices.tolist(),
                        values=sparse.values.tolist(),
                    ),
                },

                # Preserve the original metadata and text.
                payload=record.payload,
            )

            points.append(point)

        # [E10-B3.5] Insert the completed points.
        #
        # Upsert updates an existing ID rather than
        # creating a duplicate.
        client.upsert(
            collection_name=HYBRID_COLLECTION,
            points=points,
            wait=True,
        )

        copied += len(points)

        print(f"Hybrid points processed: {copied}")

        # Continue from the next source page.
        offset = next_offset

        if offset is None:
            break

    return copied