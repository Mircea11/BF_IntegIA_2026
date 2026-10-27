import json
from pathlib import Path

from transformers import AutoTokenizer

from rag_hopital.config import settings
from rag_hopital.etl.chunk import chunk_document

source = next(Path("data/conversions").glob("*.docx.json"))

metadata = json.loads(
    Path("data/hopital/hopital_documents.json").read_text()
)

info = next(item for item in metadata if item["document"] == source.name.removesuffix(".json"))
print("Available metadata fields:")
for key, value in info.items():
    print(f"  {key}: {value}")
chunks = chunk_document(
    source,
    patient_name=info["patient_name"],
    patient_ipp=info["patient_ipp"],
)

tokenizer = AutoTokenizer.from_pretrained(settings.embedder_path, local_files_only=True)
lengths = [len(tokenizer.encode(text)) for text in chunks]

print("Document:", source.name)
print("Number of chunks:", len(chunks))
print("Maximum tokens:", max(lengths))
print("First chunk:\n", chunks[0][:400])

assert max(lengths) <= 512, "A chunk exceeds 512 tokens"