"""Instructor alignment: normalized hash flags formatting variants, but preview keeps them."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_duplicates import normalized_hash_groups, build_preview, normalize, shingles, jaccard

class TestInstructorAlignment(unittest.TestCase):
    def test_teacher_normalization_ligatures(self):
        self.assertEqual(normalize("L'éléphant marche sur des oeufs."),
                         normalize("L elephant marche sur des œufs!"))

    def test_teacher_jaccard(self):
        a = shingles("A B C D", 2)
        b = shingles("A B D C", 2)
        self.assertAlmostEqual(jaccard(a,b), 1/5)

    def test_normalized_duplicate_audit_only(self):
        rows = [
            dict(chunk_id='a::0', document='a', patient_ipp='123', text='Dose 2.5 mg'),
            dict(chunk_id='a::1', document='a', patient_ipp='123', text='Dose 2 5 mg'),
        ]
        _, variants, empty = normalized_hash_groups(rows)
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]['distinct_raw_texts'], 2)
        preview, excluded, _ = build_preview(rows, 'same-document')
        self.assertEqual(len(preview), 2)  # medically different raw text stays distinct
        self.assertEqual(excluded, [])
        self.assertEqual(empty, 0)

if __name__ == '__main__': unittest.main()
