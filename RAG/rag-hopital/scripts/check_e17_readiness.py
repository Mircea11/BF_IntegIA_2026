"""E17 read-only preflight: verify model endpoint, Qdrant and Python MMR API."""
from urllib.request import urlopen
from rag_hopital.config import settings
from rag_hopital.etl.index import HYBRID_COLLECTION
from qdrant_client import QdrantClient, models

print('Embedding endpoint:', settings.embeddings_url)
print('Model identifier:', settings.embedder_path)
print('Qdrant:', settings.qdrant_url)
print('Python MMR:', hasattr(models, 'Mmr'))
print('Python NearestQuery:', hasattr(models, 'NearestQuery'))

client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
print('Hybrid collection exists:', client.collection_exists(HYBRID_COLLECTION))
if client.collection_exists(HYBRID_COLLECTION):
    print('Hybrid point count:', client.count(HYBRID_COLLECTION, exact=True).count)

try:
    with urlopen(settings.embeddings_url.rstrip('/') + '/models', timeout=4) as response:
        print('Embedding /models HTTP status:', response.status)
except Exception as exc:
    print('Embedding server is not ready:', type(exc).__name__, str(exc))
