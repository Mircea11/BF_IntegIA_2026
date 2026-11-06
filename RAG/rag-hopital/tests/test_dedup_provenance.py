"""Run: python -m unittest discover -s tests -p test_dedup_provenance.py -v"""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_duplicates import build_preview
from validate_dedup_preview import validate


def make(document, index, patient, text, date, title):
    return {
        "document": document,
        "chunk_id": f"{document}::{index}",
        "chunk_index": index,
        "patient_ipp": patient,
        "patient_name": None,
        "date": date,
        "title": title,
        "doc_type": "consultation",
        "text": text,
    }


class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.text = "Le patient présente une tension stable. Observation clinique."
        self.rows = [
            make("a.docx", 0, "101", self.text, "2026-01-03", "A"),
            make("a.docx", 1, "101", self.text, "2026-01-03", "A"),
            make("b.docx", 0, "101", self.text, "2026-01-04", "B"),
            make("c.docx", 0, "102", self.text, "2026-01-05", "C"),
            make("notice1.docx", 0, None, self.text, "2026-01-06", "N1"),
            make("notice2.docx", 0, None, self.text, "2026-01-06", "N2"),
            make("a.docx", 2, "101", self.text + " Nouvelle note.", "2026-01-03", "A"),
        ]
        self.before = copy.deepcopy(self.rows)

    def test_default_scope_only_same_document(self):
        preview, excluded, groups = build_preview(self.rows, "same-document")
        self.assertEqual(len(preview), 6)
        self.assertEqual(len(excluded), 1)
        self.assertEqual(len(groups), 1)
        self.assertEqual(preview[0]["source_chunk_ids"], ["a.docx::0", "a.docx::1"])
        self.assertEqual(preview[0]["duplicate_count"], 1)
        self.assertEqual(validate(self.rows, preview, "same-document")["status"], "PASS")
        self.assertEqual(self.rows, self.before)

    def test_cross_doc_opt_in_same_patient_and_full_metadata(self):
        preview, excluded, groups = build_preview(self.rows, "same-patient")
        self.assertEqual(len(preview), 5)
        self.assertEqual(len(excluded), 2)
        self.assertEqual(len(groups), 1)
        self.assertEqual(preview[0]["source_document_count"], 2)
        self.assertEqual(preview[0]["occurrence_count"], 3)
        self.assertEqual(preview[0]["source_references"][2]["date"], "2026-01-04")
        self.assertEqual(preview[0]["source_references"][2]["title"], "B")
        self.assertEqual(validate(self.rows, preview, "same-patient")["status"], "PASS")
        self.assertEqual(self.rows, self.before)

    def test_validator_rejects_missing_source_reference(self):
        preview, _, _ = build_preview(self.rows, "same-document")
        tampered = copy.deepcopy(preview)
        tampered[0]["source_references"].pop()
        with self.assertRaises(AssertionError):
            validate(self.rows, tampered, "same-document")

    def test_validator_rejects_cross_patient_merge(self):
        preview, _, _ = build_preview(self.rows, "same-patient")
        tampered = copy.deepcopy(preview)
        tampered[0]["source_references"].append({k:v for k,v in self.rows[3].items() if k!="text"})
        with self.assertRaises(AssertionError):
            validate(self.rows, tampered, "same-patient")


if __name__ == "__main__":
    unittest.main()
