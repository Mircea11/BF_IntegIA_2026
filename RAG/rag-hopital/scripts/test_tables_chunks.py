import json
from pathlib import Path

from docling_core.types.doc import DoclingDocument

filename = "4100001_2025-06-30_bilan.docx"

# Original converted document
source = Path("data/conversions") / f"{filename}.json"
doc = DoclingDocument.load_from_json(source)

print("Tables detected:", len(doc.tables))

# Inspect extracted table
markdown = doc.export_to_markdown()
position = markdown.find("|")

if position >= 0:
    print("\nExtracted table:")
    print(markdown[position:position + 800])

# Inspect indexed-ready chunks
print("\nCorresponding chunks:")

with Path("data/chunks/chunks.jsonl").open(encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)

        if record["document"] == filename:
            print(f"\nChunk {record['chunk_index']}:")
            print(record["text"][:800])