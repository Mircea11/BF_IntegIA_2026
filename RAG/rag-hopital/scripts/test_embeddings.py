import json
from urllib.request import Request, urlopen

from rag_hopital.config import settings

payload = {
    "model": settings.embedder_path,
    "input": "Le patient présente une insuffisance rénale chronique.",
}

request = Request(
    f"{settings.embeddings_url}/embeddings",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

with urlopen(request, timeout=30) as response:
    result = json.load(response)

embedding = result["data"][0]["embedding"]

print("Model:", result["model"])
print("Dimensions:", len(embedding))
print("Embedding generated:", bool(embedding))