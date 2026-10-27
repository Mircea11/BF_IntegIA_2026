import argparse
import json

from pathlib import Path
from transformers import AutoTokenizer

from rag_hopital.config import PROJECT_ROOT, settings
from rag_hopital.etl.chunk import chunk_document


parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=None)
args = parser.parse_args()

metadata_path = settings.corpus_path / "hopital_documents.json"
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

if args.limit is not None:
    metadata = metadata[:args.limit]

tokenizer = AutoTokenizer.from_pretrained(
    settings.embedder_path,
    local_files_only=True,
)

output = PROJECT_ROOT / "data/chunks/chunks.jsonl"
output.parent.mkdir(parents=True, exist_ok=True)

total_chunks = 0
max_tokens = 0

with output.open("w", encoding="utf-8") as f:
    for info in metadata:
        source = PROJECT_ROOT / "data/conversions" / f"{info['document']}.json"

        chunks = chunk_document(
            source,
            patient_name=info["patient_name"],
            patient_ipp=info["patient_ipp"],
            tokenizer=tokenizer,
        )

        for index, text in enumerate(chunks):
            token_count = len(tokenizer.encode(text))
            assert token_count <= 512, f"Chunk exceeds 512 tokens: {source}"

            record = {
                **info,
                "chunk_id": f"{info['document']}::{index}",
                "chunk_index": index,
                "text": text,
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")

            total_chunks += 1
            max_tokens = max(max_tokens, token_count)

print("Documents processed:", len(metadata))
print("Total chunks:", total_chunks)
print("Maximum tokens:", max_tokens)
print("Output:", output)