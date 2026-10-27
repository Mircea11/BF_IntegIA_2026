from pathlib import Path
from docling_core.types.doc import DoclingDocument

files = sorted(Path("data/conversions").glob("*.json"))

documents_with_tables = []
documents_with_images = []

for path in files:
    doc = DoclingDocument.load_from_json(path)

    if doc.tables:
        documents_with_tables.append(path.name)

    if doc.pictures:
        documents_with_images.append(path.name)

print("Documents examinés:", len(files))
print("Documents avec tableaux:", len(documents_with_tables))
print("Documents avec images:", len(documents_with_images))

print("\nExemples avec tableaux:")
print(*documents_with_tables[:5], sep="\n")

print("\nExemples avec images:")
print(*documents_with_images[:5], sep="\n")