#!/usr/bin/env python3
"""Verify the preview is lossless in PROVENANCE (not in indexed point count).

Only reads JSONL files. Does not index, modify files, or call servers.
Usage: python scripts/validate_dedup_preview.py
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    records = []
    with path.open(encoding="utf-8") as file:
        for lineno, line in enumerate(file, 1):
            if line.strip():
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"{path}:{lineno}: JSON object required")
                records.append(obj)
    return records


def validate(original: list[dict], preview: list[dict], scope: str) -> dict:
    if scope not in {"same-document", "same-patient"}:
        raise ValueError(f"Unrecognized scope: {scope}")

    original_ids = [row.get("chunk_id") for row in original]
    if None in original_ids or len(set(original_ids)) != len(original_ids):
        raise AssertionError("Original must have unique non-null chunk_id values")
    original_by_id = {row["chunk_id"]: row for row in original}
    mapped_ids = []
    groups_multi_doc = 0

    preview_ids = [row.get("chunk_id") for row in preview]
    if len(preview_ids) != len(set(preview_ids)):
        raise AssertionError("Preview includes duplicate retained chunk_id values")

    for row in preview:
        primary_id = row["chunk_id"]
        if primary_id not in original_by_id:
            raise AssertionError(f"Unknown retained chunk: {primary_id}")
        original_primary = original_by_id[primary_id]
        if row.get("text") != original_primary.get("text"):
            raise AssertionError(f"Text changed in retained chunk: {primary_id}")
        # All baseline metadata must remain, including primary document/date.
        for key, value in original_primary.items():
            if row.get(key) != value:
                raise AssertionError(f"Primary source metadata altered: {primary_id}, key={key}")

        refs = row.get("source_references")
        if not isinstance(refs, list) or not refs:
            raise AssertionError(f"Missing source_references: {primary_id}")
        if refs[0].get("chunk_id") != primary_id:
            raise AssertionError(f"First source must be retained chunk: {primary_id}")

        group_doc_names = set()
        known_patient_ids = set()
        missing_patient = False
        for ref in refs:
            source_id = ref.get("chunk_id")
            if source_id not in original_by_id:
                raise AssertionError(f"Unknown source reference: {source_id}")
            src = original_by_id[source_id]
            if row["text"] != src["text"]:
                raise AssertionError(f"Different raw text merged: {source_id} -> {primary_id}")
            expected_ref = {k: v for k, v in src.items() if k != "text"}
            if ref != expected_ref:
                raise AssertionError(f"Source metadata not preserved: {source_id}")
            mapped_ids.append(source_id)
            group_doc_names.add(str(src["document"]))
            patient_id = str(src.get("patient_ipp") or "").strip()
            if patient_id:
                known_patient_ids.add(patient_id)
            else:
                missing_patient = True
        if len(known_patient_ids) > 1 or (missing_patient and known_patient_ids):
            raise AssertionError(f"Cross-patient merge detected: {primary_id}")
        if len(group_doc_names) > 1:
            groups_multi_doc += 1
            if scope == "same-document":
                raise AssertionError(f"Cross-document merge in safe scope: {primary_id}")
            if missing_patient or not known_patient_ids:
                raise AssertionError(f"Cross-document merge without known patient: {primary_id}")

        if row.get("source_chunk_ids") != [r["chunk_id"] for r in refs]:
            raise AssertionError(f"source_chunk_ids inconsistent: {primary_id}")
        expected_docs = list(dict.fromkeys(str(r["document"]) for r in refs))
        if row.get("source_documents") != expected_docs:
            raise AssertionError(f"source_documents inconsistent: {primary_id}")
        if row.get("source_document_count") != len(expected_docs):
            raise AssertionError(f"source_document_count inconsistent: {primary_id}")
        if row.get("occurrence_count") != len(refs):
            raise AssertionError(f"occurrence_count inconsistent: {primary_id}")
        if row.get("duplicate_count") != len(refs) - 1:
            raise AssertionError(f"duplicate_count inconsistent: {primary_id}")
        if row.get("text_sha256") != hashlib.sha256(row["text"].encode()).hexdigest():
            raise AssertionError(f"SHA-256 changed: {primary_id}")

    counts = Counter(mapped_ids)
    missing = set(original_ids) - set(mapped_ids)
    extra = set(mapped_ids) - set(original_ids)
    duplicated = [key for key, count in counts.items() if count != 1]
    if missing or extra or duplicated:
        raise AssertionError(f"Incomplete provenance: missing={sorted(missing)[:5]}, "
                             f"extra={sorted(extra)[:5]}, duplicate refs={duplicated[:5]}")

    return {
        "original_chunks": len(original),
        "retained_chunks": len(preview),
        "merged_occurrences": len(original) - len(preview),
        "groups_multi_document": groups_multi_doc,
        "source_references_checked": len(mapped_ids),
        "status": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source traceability of preview")
    parser.add_argument("--chunks", default="data/chunks/chunks.jsonl")
    parser.add_argument("--preview", default="data/chunks/chunks_dedup_preview.jsonl")
    parser.add_argument("--preview-scope", default="same-document",
                        choices=("same-document", "same-patient"))
    args = parser.parse_args()
    result = validate(load_jsonl(Path(args.chunks)), load_jsonl(Path(args.preview)), args.preview_scope)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("Validation réussie : chaque chunk original apparaît une et une seule fois "
          "dans les références de provenance.")


if __name__ == "__main__":
    main()
