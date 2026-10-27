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