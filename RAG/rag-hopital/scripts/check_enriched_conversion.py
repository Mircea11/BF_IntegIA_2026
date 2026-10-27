from pathlib import Path
from docling_core.types.doc import DoclingDocument

source = Path(
    "data/conversions_enriched/"
    "4100017_2025-11-02_imagerie.pdf.json"
)

doc = DoclingDocument.load_from_json(source)

print("Pages:", len(doc.pages))
print("Text elements:", len(doc.texts))
print("Tables:", len(doc.tables))
print("Pictures:", len(doc.pictures))

print("\nExtracted text:")
print(doc.export_to_text()[:1000])