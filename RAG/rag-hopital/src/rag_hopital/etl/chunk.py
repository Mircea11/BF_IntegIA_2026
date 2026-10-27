from pathlib import Path

from docling_core.types.doc import DoclingDocument
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

from rag_hopital.config import settings


def chunk_document(json_path: Path, patient_name=None, patient_ipp=None, tokenizer=None):
    """Split a converted document into chunks of at most 512 tokens."""

    doc = DoclingDocument.load_from_json(str(json_path))

    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(
            settings.embedder_path,
            local_files_only=True,
        )

    patient_line = ""
    if patient_ipp:
        patient_line = f"Patient: {patient_name} | IPP: {patient_ipp}\n"

    # Reserve space for patient identification.
    reserved = len(tokenizer.encode(patient_line, add_special_tokens=False)) + 8

    docling_tokenizer = HuggingFaceTokenizer(
        tokenizer=tokenizer,
        max_tokens=512 - reserved,
    )

    chunker = HybridChunker(tokenizer=docling_tokenizer)

    return [
        patient_line + chunker.contextualize(chunk)
        for chunk in chunker.chunk(doc)
    ]