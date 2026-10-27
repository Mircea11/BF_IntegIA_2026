from pathlib import Path

from rag_hopital.etl.convert import (
    create_converter,
    convert_document,
)

# Select a PDF from the existing corpus
source = next(
    (
        p for p in Path("data/hopital").rglob("*")
        if p.is_file() and p.suffix.lower() == ".pdf"
    ),
    None,
)

if source is None:
    raise FileNotFoundError("Aucun PDF trouvé dans data/hopital")

# Separate output: preserve the original conversions
output_dir = Path("data/conversions_enriched")

converter = create_converter(
    describe_pictures=False
)

output = convert_document(
    source,
    output_dir,
    converter=converter,
)

print("Source:", source.name)
print("Output:", output)