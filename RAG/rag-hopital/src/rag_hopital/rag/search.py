from rag_hopital.etl.index import (
    COLLECTION,
    connect_qdrant,
    embed_texts,
)


def search(query: str, top_k: int = 5):
    """Search Qdrant using BGE-M3 embeddings."""

    vector = embed_texts([query])[0]

    client = connect_qdrant()

    response = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=top_k,
        with_payload=True,
    )

    return response.points