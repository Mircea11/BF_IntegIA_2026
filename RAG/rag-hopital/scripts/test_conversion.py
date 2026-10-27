from pathlib import Path
from rag_hopital.etl.convert import convert_document

source = next(Path("data/hopital").rglob("*.docx"))
output = convert_document(source, Path("data/conversions"))

print("Source:", source.name)
print("Converted:", output)