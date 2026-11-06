#!/usr/bin/env python3
"""RAG Hôpital — non-destructive duplicate audit BEFORE Qdrant indexing.

Read existing data/chunks/chunks.jsonl and original files in data/hopital.
Write reports only; DO NOT modify input, Qdrant, PostgreSQL, or active models.

Usage: python scripts/audit_duplicates.py
Optional: python scripts/audit_duplicates.py --emit-safe-copy
Optional reviewed experiment: --emit-safe-copy --preview-scope same-patient
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

try:
    from unidecode import unidecode
except ImportError:
    import unicodedata
    def unidecode(text: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFKD", text)
                       if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """Retain word boundaries; case/accents/punctuation differences are ignored."""
    return " ".join(re.findall(r"\w+", unidecode(text.casefold())))


def shingles(text: str, k: int) -> set[tuple[str, ...]]:
    words = normalize(text).split()
    return {tuple(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def without_patient_header(text: str) -> str:
    """For approximate similarity only; NEVER strip identity for exact hashes."""
    lines = text.split("\n", 1)
    if len(lines) == 2 and lines[0].strip().lower().startswith("patient:"):
        return lines[1]
    return text


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def exact_groups(items: list[dict], field: str, label: str) -> list[dict]:
    by_hash = defaultdict(list)
    for item in items:
        by_hash[item[field]].append(item)
    rows = []
    for hash_value, group in sorted(by_hash.items()):
        if len(group) > 1:
            rows.append({
                "hash": hash_value,
                "copies": len(group),
                "ids": " | ".join(item[label] for item in group),
                "patients": " | ".join(sorted({str(item.get("patient_ipp") or "N/A") for item in group})),
            })
    return sorted(rows, key=lambda r: (-r["copies"], r["ids"]))


def normalized_hash_groups(chunks: list[dict]) -> tuple[list[dict], list[dict], int]:
    """Find exact matches AFTER text normalization (inspection only).

    The raw-text SHA-256 remains the ONLY allowed consolidation fingerprint.
    In particular, normalizing punctuation could turn medically different
    values into identical strings. Skip empty normalized texts.
    """
    by_normalized = defaultdict(list)
    empty_count = 0
    for item in chunks:
        normalized = normalize(str(item["text"]))
        if not normalized:
            empty_count += 1
            continue
        by_normalized[fingerprint(normalized.encode("utf-8"))].append(item)

    rows = []
    variants = []
    for normalized_hash, group in sorted(by_normalized.items()):
        if len(group) < 2:
            continue
        raw_hashes = {fingerprint(str(item["text"]).encode("utf-8")) for item in group}
        docs = list(dict.fromkeys(str(item["document"]) for item in group))
        row = {
            "normalized_sha256": normalized_hash,
            "copies": len(group),
            "distinct_raw_texts": len(raw_hashes),
            "format_variants": len(raw_hashes) > 1,
            "ids": " | ".join(str(item["chunk_id"]) for item in group),
            "documents": " | ".join(docs),
            "patients": " | ".join(sorted({str(item.get("patient_ipp") or "N/A") for item in group})),
        }
        rows.append(row)
        if row["format_variants"]:
            variants.append(row)
    rows.sort(key=lambda x: (-x["copies"], x["ids"]))
    variants.sort(key=lambda x: (-x["copies"], x["ids"]))
    return rows, variants, empty_count


def approximate_pairs(items: list[dict], k: int, lsh_threshold: float,
                      min_shingles: int, num_perm: int = 128) -> tuple[list[dict], int, int]:
    """LSH proposes candidate pairs; true Jaccard scores each candidate.

    This is a probabilistic *screen*: LSH cannot guarantee recall of all pairs.
    """
    try:
        from datasketch import MinHash, MinHashLSH
    except ImportError as exc:
        raise SystemExit(
            "Module manquant : datasketch. Installer dans le .venv avec "
            "'python -m pip install datasketch' ou relancer avec --skip-lsh "
            "(audit des doublons exacts seulement)."
        ) from exc
    lsh = MinHashLSH(threshold=lsh_threshold, num_perm=num_perm)
    saved = {}
    rows = []
    omitted = 0
    candidates_seen = 0

    for ix, item in enumerate(items):
        sk = shingles(item["comparison_text"], k)
        if len(sk) < min_shingles:
            omitted += 1
            continue
        signature = MinHash(num_perm=num_perm)
        for gram in sorted(sk):
            signature.update("\x1f".join(gram).encode("utf-8"))
        # Compare before inserting this item, so each pair is considered once.
        for prev_idx_string in lsh.query(signature):
            prior, prior_shingles = saved[int(prev_idx_string)]
            candidates_seen += 1
            score = jaccard(prior_shingles, sk)
            rows.append({
                "id_a": prior["id"],
                "id_b": item["id"],
                "document_a": prior["document"],
                "document_b": item["document"],
                "patient_a": prior.get("patient_ipp") or "",
                "patient_b": item.get("patient_ipp") or "",
                "same_document": prior["document"] == item["document"],
                "cross_patient": bool(prior.get("patient_ipp") and item.get("patient_ipp") and
                                      prior["patient_ipp"] != item["patient_ipp"]),
                "jaccard": round(score, 6),
                "shingles_a": len(prior_shingles),
                "shingles_b": len(sk),
            })
        lsh.insert(str(ix), signature)
        saved[ix] = (item, sk)

    rows.sort(key=lambda r: (-r["jaccard"], r["id_a"], r["id_b"]))
    return rows, omitted, candidates_seen


PROVENANCE_VERSION = 2


def patient_identity(item: dict) -> str:
    """Missing IPP is NOT evidence that two records have the same patient."""
    return str(item.get("patient_ipp") or "").strip()


def merge_key(item: dict, scope: str) -> tuple:
    """Only byte-for-byte identical text is eligible for the preview.

    The safe scope is SAME DOCUMENT + SAME PATIENT identity (or both unassigned).
    Optional same-patient scope allows cross-document merging only with known IPP.
    """
    ipp = patient_identity(item)
    if scope == "same-patient" and ipp:
        return ("known_patient", ipp, item["text"])
    return ("document", str(item["document"]), ipp, item["text"])


def source_reference(original: dict) -> dict:
    """Preserve EVERY original metadata field at the source level, but not the long text.

    Examples: document, chunk_id, chunk_index, patient_ipp, date, title,
    doc_type, care_path and service. This prevents loss of temporal attribution.
    """
    return {key: val for key, val in original.items() if key != "text"}


def build_preview(rows: list[dict], scope: str) -> tuple[list[dict], list[dict], list[dict]]:
    """Consolidate exact-text occurrences and attach provenance to retained points.

    Does not mutate the incoming records or any original file.
    """
    if scope not in {"same-document", "same-patient"}:
        raise ValueError("Preview scope must be 'same-document' or 'same-patient'")

    groups = {}  # insertion order preserves the existing chunk order
    for item in rows:
        groups.setdefault(merge_key(item, scope), []).append(item)

    preview, excluded, merged_groups = [], [], []
    for group in groups.values():
        primary = dict(group[0])
        references = [source_reference(item) for item in group]
        source_docs = list(dict.fromkeys(str(item["document"]) for item in group))

        # Existing fields chunk_id / document / patient_* / date remain those
        # of the primary source for compatibility with existing RAG code.
        primary.update({
            "provenance_schema_version": PROVENANCE_VERSION,
            "source_references": references,
            "source_chunk_ids": [str(item["chunk_id"]) for item in group],
            "source_documents": source_docs,
            "source_document_count": len(source_docs),
            "occurrence_count": len(group),
            "duplicate_count": len(group) - 1,
            "text_sha256": fingerprint(primary["text"].encode("utf-8")),
        })
        preview.append(primary)

        if len(group) == 1:
            continue

        merged_groups.append({
            "retained_chunk_id": primary["chunk_id"],
            "occurrences": len(group),
            "source_document_count": len(source_docs),
            "source_documents": " | ".join(source_docs),
            "source_chunk_ids": " | ".join(primary["source_chunk_ids"]),
            "patient_ipp": patient_identity(primary),
            "source_dates": " | ".join(str(item.get("date") or "") for item in group),
        })
        for original in group[1:]:
            excluded.append({
                "removed_chunk_id": original["chunk_id"],
                "retained_chunk_id": primary["chunk_id"],
                "removed_document": original["document"],
                "retained_document": primary["document"],
                "patient_ipp": patient_identity(original),
                "removed_date": str(original.get("date") or ""),
                "reason": "same document, identical text" if
                     original["document"] == primary["document"] else
                     "same known patient, cross-document identical text (OPT-IN)",
            })

    return preview, excluded, merged_groups


def emit_safe_copy(input_rows: list[dict], target: Path, audit_path: Path,
                   groups_path: Path, scope: str, source: Path) -> dict:
    """Write a SEPARATE JSONL preview plus exclusions and complete provenance.

    No source files, Qdrant, PostgreSQL, or model endpoints are modified.
    """
    if target.resolve() == source.resolve():
        raise ValueError("Refusing to overwrite the original chunks file")
    target.parent.mkdir(parents=True, exist_ok=True)
    preview, exclusions, merged_groups = build_preview(input_rows, scope)
    with target.open("w", encoding="utf-8") as f:
        for record in preview:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    write_csv(audit_path, ["removed_chunk_id", "retained_chunk_id",
                           "removed_document", "retained_document",
                           "patient_ipp", "removed_date", "reason"], exclusions)
    write_csv(groups_path, ["retained_chunk_id", "occurrences",
                            "source_document_count", "source_documents",
                            "source_chunk_ids", "patient_ipp", "source_dates"], merged_groups)
    return {
        "original_count": len(input_rows),
        "retained_count": len(preview),
        "excluded_count": len(exclusions),
        "groups_merged": len(merged_groups),
        "groups_cross_document": sum(g["source_document_count"] > 1 for g in merged_groups),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Non-destructive pre-Qdrant duplicate audit")
    parser.add_argument("--chunks", default="data/chunks/chunks.jsonl")
    parser.add_argument("--sources", default="data/hopital")
    parser.add_argument("--reports", default="reports/dedup_audit")
    parser.add_argument("--k", type=int, default=3, help="Word shingle size")
    parser.add_argument("--lsh-threshold", type=float, default=0.65,
                        help="LSH candidate-screening threshold, not a dedup rule")
    parser.add_argument("--min-shingles", type=int, default=8)
    parser.add_argument("--emit-safe-copy", action="store_true",
                        help="Write a separate preview with full provenance metadata")
    parser.add_argument("--preview-scope", choices=("same-document", "same-patient"),
                        default="same-document", help="Default: only within the same document. "
                        "Same-patient allows cross-document exact matches with known IPP (opt-in)")
    parser.add_argument("--skip-lsh", action="store_true", help="Run only exact SHA-256 audit, "
                        "without datasketch / approximate-similarity screening")
    args = parser.parse_args()

    if args.k < 1 or not 0 < args.lsh_threshold < 1 or args.min_shingles < 1:
        parser.error("Expected k >= 1, 0 < lsh-threshold < 1, min-shingles >= 1")
    if args.preview_scope == "same-patient" and not args.emit_safe_copy:
        parser.error("--preview-scope same-patient requires --emit-safe-copy")
    chunks_path = Path(args.chunks)
    if not chunks_path.is_file():
        parser.error(f"Missing {chunks_path}. Use the EXISTING chunk export, do not reindex.")
    source_path = Path(args.sources)
    out = Path(args.reports)
    out.mkdir(parents=True, exist_ok=True)

    original_chunks = []
    with chunks_path.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if any(key not in obj for key in ("document", "chunk_id", "text")):
                raise ValueError(f"Missing document/chunk_id/text in line {line_num}")
            original_chunks.append(obj)

    # Exact file-level hashes: binary identity, without extracting/rewriting files.
    original_files = []
    if source_path.is_dir():
        for path in sorted(source_path.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".docx", ".pdf"}:
                original_files.append({
                    "id": path.name, "document": path.name,
                    "sha256": fingerprint(path.read_bytes()),
                })

    file_exact = exact_groups(original_files, "sha256", "id")
    write_csv(out / "documents_exact_sha256.csv", ["hash", "copies", "ids", "patients"], file_exact)

    chunk_items = [{
        "id": item["chunk_id"],
        "document": item["document"],
        "patient_ipp": str(item.get("patient_ipp") or ""),
        "comparison_text": without_patient_header(item["text"]),
        "sha256": fingerprint(item["text"].encode("utf-8")),
    } for item in original_chunks]
    chunk_exact = exact_groups(chunk_items, "sha256", "id")
    write_csv(out / "chunks_exact_sha256.csv", ["hash", "copies", "ids", "patients"], chunk_exact)

    # Instructor 07: normalized-text hashes detect superficial textual differences
    # (case, spacing, punctuation, accent/ligature). This is AUDIT ONLY.
    # Text normalization can also erase clinically important distinctions
    # (e.g. decimal punctuation); NEVER merge using this hash alone.
    normalized_groups, normalized_variants, empty_normalized = normalized_hash_groups(
        original_chunks
    )
    normalized_columns = ["normalized_sha256", "copies", "distinct_raw_texts",
                          "format_variants", "ids", "documents", "patients"]
    write_csv(out / "chunks_normalized_sha256.csv", normalized_columns,
              normalized_groups)
    write_csv(out / "chunks_normalized_format_variants.csv", normalized_columns,
              normalized_variants)

    # Group chunks per document and approximate original document textual content.
    # The chunks are already contextualized; this is a screening, NOT canonical extraction.
    grouped = defaultdict(list)
    for original in original_chunks:
        grouped[original["document"]].append(original)
    documents = []
    for doc, group in sorted(grouped.items()):
        group.sort(key=lambda x: int(x.get("chunk_index", 0)))
        documents.append({
            "id": doc, "document": doc,
            "patient_ipp": str(group[0].get("patient_ipp") or ""),
            "comparison_text": "\n".join(without_patient_header(c["text"]) for c in group),
        })

    if args.skip_lsh:
        doc_pairs, doc_skipped, doc_candidates = [], 0, 0
        chunk_pairs, chunk_skipped, chunk_candidates = [], 0, 0
    else:
        doc_pairs, doc_skipped, doc_candidates = approximate_pairs(
            documents, args.k, args.lsh_threshold, args.min_shingles)
        chunk_pairs, chunk_skipped, chunk_candidates = approximate_pairs(
            chunk_items, args.k, args.lsh_threshold, args.min_shingles)
    columns = ["id_a", "id_b", "document_a", "document_b", "patient_a", "patient_b",
               "same_document", "cross_patient", "jaccard", "shingles_a", "shingles_b"]
    write_csv(out / "documents_similar_lsh_candidates.csv", columns, doc_pairs)
    write_csv(out / "chunks_similar_lsh_candidates.csv", columns, chunk_pairs)

    def n_ge(rows: list[dict], cutoff: float) -> int:
        return sum(row["jaccard"] >= cutoff for row in rows)

    # Create a *separate* candidate file. Never overwrite the working chunk export.
    preview_stats = None
    if args.emit_safe_copy:
        preview_stats = emit_safe_copy(
            original_chunks, Path("data/chunks/chunks_dedup_preview.jsonl"),
            out / "chunks_preview_exclusions.csv", out / "preview_merged_groups.csv",
            args.preview_scope, chunks_path)

    summary = [
        "# RAG Hôpital — Audit des doublons (AVANT Qdrant)",
        "",
        "## Méthode",
        f"- Chunks existants : `{chunks_path}` (lecture seule).",
        f"- Fichiers source : `{source_path}` (lecture seule).",
        "- Documents exacts : SHA-256 sur les octets DOCX/PDF originaux.",
        "- Chunks exacts : SHA-256 sur le texte brut, avec ligne patient.",
        "- Chunks identiques APRÈS normalisation : SHA-256 du texte normalisé : audit seulement, ",
        "  aucune fusion fondée sur ce hash (la ponctuation et les décimales peuvent être significatives).",
        f"- Doublons approximatifs : shingles de {args.k} mots normalisés, ",
        f"  MinHash/LSH (seuil de candidats {args.lsh_threshold}) puis Jaccard EXACT des candidats.",
        "- Pour la similarité seulement, la ligne patient ajoutée au chunk est ignorée.",
        "- LSH est probabiliste : des paires similaires peuvent ne pas être proposées.",
        "- Aucun chunk et aucun document n'est supprimé des sources, aucun index modifié.",
        "",
        "## Résultats",
        f"- Fichiers DOCX/PDF examinés : **{len(original_files)}**.",
        f"- Groupes de fichiers identiques (SHA-256) : **{len(file_exact)}**.",
        f"- Documents reconstruits des chunks : **{len(documents)}**.",
        f"- Chunks examinés : **{len(chunk_items)}**.",
        f"- Groupes de chunks strictement identiques : **{len(chunk_exact)}**.",
        f"- Groupes de chunks identiques après normalisation : **{len(normalized_groups)}**.",
        f"- Dont groupes avec textes bruts DISTINCTS (variantes de format ou autre) : **{len(normalized_variants)}**.",
        f"- Chunks à normalisation vide exclus de ce hash : {empty_normalized}.",
        "- Variantes normalisées à examiner : `reports/dedup_audit/chunks_normalized_format_variants.csv`.",
        f"- Documents écartés de l'audit LSH (trop courts) : {doc_skipped}.",
        f"- Chunks écartés de l'audit LSH (trop courts) : {chunk_skipped}.",
        f"- Écran LSH : {'désactivé (audit exact uniquement)' if args.skip_lsh else 'activé, probabiliste'}.",
        f"- Paires de documents candidates LSH : **{doc_candidates}**.",
        f"- Paires de chunks candidates LSH : **{chunk_candidates}**.",
        f"- Paires de documents Jaccard >= 0.80 parmi les candidates : **{n_ge(doc_pairs, 0.8)}**.",
        f"- Paires de chunks Jaccard >= 0.80 parmi les candidates : **{n_ge(chunk_pairs, 0.8)}**.",
        f"- Paires de chunks Jaccard >= 0.90 parmi les candidates : **{n_ge(chunk_pairs, 0.9)}**.",
        f"- Paires de chunks cross-patient >= 0.80 parmi les candidates : **{sum(r['cross_patient'] and r['jaccard']>=0.8 for r in chunk_pairs)}**.",
    ]
    if preview_stats is not None:
        summary += [
            f"- Portée de la consolidation expérimentale : **{args.preview_scope}**.",
            f"- Chunks dans la copie : **{preview_stats['retained_count']}**.",
            f"- Occurrences fusionnées dans la copie uniquement : **{preview_stats['excluded_count']}**.",
            f"- Groupes fusionnés : **{preview_stats['groups_merged']}**, "
            f"dont **{preview_stats['groups_cross_document']}** multi-documents.",
            "- Chaque chunk conservé porte `source_references` (toutes les occurrences, "
            "avec `document`, `chunk_id`, `date`, `patient_ipp`, `title`, etc.), "
            "`source_documents`, `source_chunk_ids` et `duplicate_count`.",
            "- Copie distincte : `data/chunks/chunks_dedup_preview.jsonl`.",
            "- Audit des regroupements : `reports/dedup_audit/preview_merged_groups.csv`.",
            "- Contrôle obligatoire : `python scripts/validate_dedup_preview.py`.",
        ]

    summary += ["", "## Vérifications supplémentaires du cours 07", "",
                "- Hash normalisé : détecte des variantes textuelles ; aucune suppression automatique.",
                "- Le formateur illustre les bigrammes (`--k 2`) et un seuil LSH de 0.2 "
                "sur quatre petits textes ; les réglages par défaut de cet audit de corpus sont "
                "des trigrammes et un seuil de 0.65 pour limiter le volume de candidats.",
                "- MMR agit à la recherche (dense + sparse → RRF → MMR), et non "
                "sur le corpus avant Qdrant. Prévoir une expérience séparée après cet audit.",
                "- Les résultats Jaccard affichés sont EXACTS pour les paires proposées par LSH, "
                "mais LSH ne garantit pas de retrouver toutes les paires.", ""]

    for title, rows in (("Documents les plus similaires", doc_pairs),
                        ("Chunks les plus similaires", chunk_pairs)):
        summary += ["", f"## {title}", "", "| ID A | ID B | Jaccard | Patients différents ? |",
                    "|---|---|---:|---|"]
        for r in rows[:12]:
            summary.append(f"| {r['id_a']} | {r['id_b']} | {r['jaccard']:.3f} | {'Oui' if r['cross_patient'] else 'Non'} |")
        if not rows:
            summary.append("Aucune paire retournée par le filtrage LSH avec ces paramètres.")

    summary += [
        "", "## Décision avant déduplication", "",
        "1. Examiner les paires à haut Jaccard : identité de patient, dates, médicaments, chiffres, négations.",
        "2. Jamais de fusion inter-patients ; fusion inter-documents uniquement en "
        "mode same-patient explicite, avec IPP connu ET texte brut identique.",
        "3. Chaque chunk consolidé conserve toutes les références sources et "
        "dates; adapter l'évaluateur au champ source_references avant une comparaison A/B.",
        "4. Si une déduplication est retenue : créer une NOUVELLE collection Qdrant, pas modifier la baseline.",
        "5. Comparer la nouvelle indexation aux métriques E11 (Hit@5, Fact Recall@5, nDCG@5).",
        "",
    ]
    (out / "SYNTHESE.md").write_text("\n".join(summary), encoding="utf-8")
    print("Audit terminé (aucune suppression, aucun accès Qdrant/PostgreSQL).")
    print(f"Sources DOCX/PDF: {len(original_files)} | documents: {len(documents)} | chunks: {len(chunk_items)}")
    print(f"Doublons exacts: {len(file_exact)} groupes de fichiers, {len(chunk_exact)} groupes de chunks")
    print(f"Après normalisation : {len(normalized_groups)} groupes; "
          f"dont {len(normalized_variants)} avec textes bruts différents (revue uniquement)")
    print(f"Paires Jaccard >= 0.80 (documents/chunks): {n_ge(doc_pairs,0.8)}/{n_ge(chunk_pairs,0.8)}")
    print(f"Comparaisons proposées par LSH (documents/chunks): {doc_candidates}/{chunk_candidates}")
    print(f"Rapport: {out / 'SYNTHESE.md'}")
    if preview_stats is not None:
        print(f"Aperçu : {preview_stats['retained_count']} chunks retenus "
              f"({preview_stats['excluded_count']} occurrences regroupées, "
              f"{preview_stats['groups_cross_document']} groupes multi-documents).")
        print("Provenance complète par chunk : source_references. Valider avant réindexation.")


if __name__ == "__main__":
    main()
