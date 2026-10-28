"""
E10-C — THREE RETRIEVAL METHODS

dense  : BGE-M3 semantic search.
sparse : BM25 lexical search.
hybrid : Dense + Sparse, combined with RRF.

All methods return Qdrant scored points.
"""

# ============================================================
# [E10-C — SECTION 0] IMPORTS
# ============================================================

# Cache the BM25 model so it is loaded only once.
from functools import lru_cache

# Local BM25 sparse embedding.
from fastembed import SparseTextEmbedding

# Qdrant query and fusion structures.
from qdrant_client import models

# Reuse the existing indexing and connection functions.
from rag_hopital.etl.index import (
    COLLECTION,
    HYBRID_COLLECTION,
    connect_qdrant,
    connect_hybrid_qdrant,
    embed_texts,
)


# ============================================================
# [E10-C — SECTION 1] LOAD THE SPARSE MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_bm25_model():
    """
    Load BM25 once and reuse it for subsequent queries.

    local_files_only=True prevents new model downloads.
    """

    return SparseTextEmbedding(
        model_name="Qdrant/bm25",
        language="french",
        local_files_only=True,
    )


# ============================================================
# [E10-C — SECTION 2] CREATE A SPARSE QUERY VECTOR
# ============================================================

def embed_sparse_query(query: str):
    """
    Convert a question into a BM25 sparse vector.

    Returns a Qdrant SparseVector containing:
    - indices: numerical identifiers of the terms;
    - values: weights associated with those terms.
    """

    # Retrieve the locally cached model.
    bm25 = get_bm25_model()

    # query_embed() prepares a search query.
    #
    # We use query_embed(), not document embed(),
    # because BM25 distinguishes query and document encoding.
    embedding = next(iter(bm25.query_embed(query)))

    # Convert NumPy arrays into Python lists.
    return models.SparseVector(
        indices=embedding.indices.tolist(),
        values=embedding.values.tolist(),
    )


# ============================================================
# [E10-C — SECTION 3] SEARCH
# ============================================================

def search(
    query: str,
    top_k: int = 5,
    *,
    method: str = "dense",
    candidates: int = 30,
):
    """
    Search Qdrant using the selected retrieval method.

    PARAMETERS
    ----------
    query:
        Question submitted by the user.

    top_k:
        Maximum number of returned chunks.

    method:
        "dense", "sparse" or "hybrid".

    candidates:
        Number of candidates retrieved from each method
        before hybrid RRF fusion.

    OUTPUT
    ------
    List of Qdrant scored points.
    """

    # --------------------------------------------------------
    # [E10-C3.1] VALIDATE THE PARAMETERS
    # --------------------------------------------------------

    if method not in {"dense", "sparse", "hybrid"}:
        raise ValueError(f"Unknown retrieval method: {method}")

    if not query.strip():
        raise ValueError("The search query cannot be empty")

    if top_k < 1 or candidates < 1:
        raise ValueError("top_k and candidates must be positive")

    # --------------------------------------------------------
    # [E10-C3.2] DENSE SEARCH — EXISTING METHOD
    # --------------------------------------------------------

    if method == "dense":

        # Use the existing BGE-M3 embedding server.
        vector = embed_texts([query])[0]

        # Search the original dense collection.
        client = connect_qdrant()

        response = client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
        )

        return response.points

    # --------------------------------------------------------
    # [E10-C3.3] SPARSE QUERY PREPARATION
    # --------------------------------------------------------

    # Both sparse and hybrid methods need BM25.
    sparse_vector = embed_sparse_query(query)

    # Connect to the populated hybrid collection.
    client = connect_hybrid_qdrant()

    # --------------------------------------------------------
    # [E10-C3.4] SPARSE-ONLY SEARCH
    # --------------------------------------------------------

    if method == "sparse":

        # Search only the BM25 vector index.
        #
        # No BGE-M3 embedding request is performed.
        response = client.query_points(
            collection_name=HYBRID_COLLECTION,
            query=sparse_vector,
            using="bm25",
            limit=top_k,
            with_payload=True,
        )

        return response.points

    # --------------------------------------------------------
    # [E10-C3.5] HYBRID SEARCH
    # --------------------------------------------------------

    # Generate the dense query vector with BGE-M3.
    dense_vector = embed_texts([query])[0]

    # Ensure each retrieval branch supplies enough candidates.
    candidate_limit = max(candidates, top_k)

    # Run two retrieval methods inside Qdrant.
    #
    # Prefetch 1: dense search.
    # Prefetch 2: sparse search.
    #
    # RRF combines their rankings.
    # The final response contains at most top_k chunks.
    response = client.query_points(
        collection_name=HYBRID_COLLECTION,

        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=candidate_limit,
            ),

            models.Prefetch(
                query=sparse_vector,
                using="bm25",
                limit=candidate_limit,
            ),
        ],

        query=models.FusionQuery(
            fusion=models.Fusion.RRF,
        ),

        limit=top_k,
        with_payload=True,
    )

    return response.points