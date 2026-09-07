"""Scope metadata never upgrades an affine or legacy witness to functional."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audit_witness_strength import audit


class IncomparabilityStrengthTests(unittest.TestCase):
    def check_record(self, **changes):
        record = {
            'id': 1, 'short_name': 'test', 'relationship_type': 'incomparable',
            'status': 'established', 'parameter_1_id': 'a', 'parameter_2_id': 'b',
            'incomparability_strength': 'affine',
            'parameter_1_larger_witness': 'A/B tends to infinity on the first family.',
            'parameter_2_larger_witness': 'B/A tends to infinity on the second family.',
            'latex_proof_label': 'cor:test', 'proof_source': 'Full survey proof: cor:test.',
        }
        record.update(changes)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'values').mkdir()
            (root / 'relationships').mkdir()
            (root / 'relationships/test.json').write_text(json.dumps(record))
            return audit(root)['incomparable'][0]

    def test_affine_certificate_uses_survey_proof_pointer(self):
        row = self.check_record()
        self.assertTrue(row['verified'])
        self.assertEqual(row['incomparability_strength'], 'affine')

    def test_legacy_scope_not_inferred(self):
        row = self.check_record(incomparability_strength=None, references='A cited source.')
        self.assertTrue(row['verified'])
        self.assertIsNone(row['incomparability_strength'])

    def test_missing_direction_or_half_proof_pointer_is_incomplete(self):
        for changes in ({'parameter_2_larger_witness': ''}, {'latex_proof_label': ''}, {'proof_source': ''}):
            self.assertFalse(self.check_record(**changes)['verified'])

    def test_unknown_scope_rejected(self):
        self.assertFalse(self.check_record(incomparability_strength='strict')['verified'])

    def test_explicit_functional_scope_is_not_automatically_assigned(self):
        row = self.check_record(incomparability_strength='functional',
                                parameter_1_larger_witness='A=n, B=1 on the first family.',
                                parameter_2_larger_witness='B=n, A=1 on the second family.')
        self.assertTrue(row['verified'])  # Presence of a certificate, not proof validation.
        self.assertEqual(row['incomparability_strength'], 'functional')


if __name__ == '__main__':
    unittest.main()
