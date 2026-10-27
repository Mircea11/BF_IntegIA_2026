from pathlib import Path
from shutil import which

from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    ImageFormatOption,
)
from docling_core.types.doc import ImageRefMode


SUPPORTED_FORMATS = {
    ".pdf",
    ".doc",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}


def create_converter(describe_pictures=False):
    """Configure OCR, table recognition and optional image descriptions."""

    options = PdfPipelineOptions()

    # OCR: scanned PDFs and images
    options.do_ocr = True

    # Recognize table structures
    options.do_table_structure = True

    # Preserve images and diagrams
    options.generate_page_images = True
    options.generate_picture_images = True
    options.images_scale = 1.5

    # Optional: interpret diagrams using a vision-language model
    options.do_picture_description = describe_pictures

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=options
            ),
            InputFormat.IMAGE: ImageFormatOption(
                pipeline_options=options
            ),
        }
    )


def convert_document(source, output_dir, converter=None, force=False):
    """Convert one document to structured Docling JSON."""

    source = Path(source)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    output = output_dir / f"{source.name}.json"

    if output.exists() and not force:
        return output

    if source.suffix.lower() == ".doc":
        if not (which("libreoffice") or which("soffice")):
            raise RuntimeError(
                "LibreOffice is required to read legacy .doc files"
            )

    converter = converter or create_converter()

    result = converter.convert(source)

    if result.status != ConversionStatus.SUCCESS:
        raise RuntimeError(
            f"Conversion failed or incomplete: {source.name} "
            f"({result.status})"
        )

    # Preserve document structure, tables and embedded images
    result.document.save_as_json(
        output,
        image_mode=ImageRefMode.EMBEDDED,
    )

    return output


def convert_corpus(
    source_dir,
    output_dir,
    limit=None,
    describe_pictures=False,
    force=False,
):
    """Convert documents, skipping existing outputs."""

    files = sorted(
        p for p in Path(source_dir).rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_FORMATS
    )

    if limit is not None:
        files = files[:limit]

    converter = create_converter(
        describe_pictures=describe_pictures
    )

    converted = 0
    skipped = 0
    errors = []

    for i, source in enumerate(files, 1):

        output = Path(output_dir) / f"{source.name}.json"

        if output.exists() and not force:
            skipped += 1
            continue

        try:
            convert_document(
                source,
                output_dir,
                converter=converter,
                force=force,
            )
            converted += 1

        except Exception as error:
            errors.append((source.name, str(error)))

        if i % 10 == 0 or i == len(files):
            print(f"Progress: {i}/{len(files)}", flush=True)

    print(f"Converted: {converted}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {len(errors)}")

    for filename, error in errors:
        print(f"FAILED: {filename}: {error}")