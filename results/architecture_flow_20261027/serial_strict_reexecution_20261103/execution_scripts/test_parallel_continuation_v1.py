import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import continue_parallel_heldout_v1 as continuation


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class DrainSealTest(unittest.TestCase):
    def fixture(self, base):
        source = base / 'frozen_input'
        source.write_text('unchanged')
        job = dict(phase='heldout', circuit='c', family='sb', seed=21, width=100,
                   roles={'p0': {'A0': {}}})
        write(base/'capacity_selection.json', {'circuits': {'c': {'size': 40}}})
        write(base/'evaluation_invocations/heldout_unstarted_recovery_v1_1_registration.json', {'jobs': [job]})
        name = 'heldout_c_s21_sb_n40_w100_p0_a0'
        directory = base/'evaluation_cases/heldout_c_s21_sb_w100'
        write(directory/'result.json', dict(status='completed', job=job,
            flows={'p0': {'status': 'completed', 'roles': {'A0': name}}}))
        write(directory/'p0_audit_summary.json', dict(passed=True, legal=[{'name': name}], failed=[]))
        manifest = dict(status='completed', shared_inputs={str(source): {
            'sha256': continuation.sha256(source), 'stat_identity': continuation.io.identity(source)}})
        for run in (name, 'heldout_c_s21_sb_n40_w100_p0_place'):
            write(base/'runs'/run/'manifest.json', manifest)
        return source, directory

    def test_reconstructs_shared_input_seal_without_overwriting_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, directory = self.fixture(base)
            previous = (directory/'result.json').read_bytes()
            with patch.object(continuation, 'BASE', base):
                continuation.seal_drained_invocation(base/'seal.json')
            seal = continuation.read(base/'seal.json')
            self.assertTrue(seal['passed'])
            self.assertEqual(len(seal['checked_runs']), 2)
            self.assertEqual(len(seal['inputs']), 1)
            self.assertEqual((directory/'result.json').read_bytes(), previous)

    def test_changed_frozen_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, _ = self.fixture(base)
            source.write_text('modified')
            with patch.object(continuation, 'BASE', base), self.assertRaises(AssertionError):
                continuation.seal_drained_invocation(base/'seal.json')
            self.assertFalse((base/'seal.json').exists())

    def test_partial_case_is_rejected_after_owner_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, directory = self.fixture(base)
            (directory/'result.json').unlink()
            with patch.object(continuation, 'BASE', base), self.assertRaises(AssertionError):
                continuation.seal_drained_invocation(base/'seal.json')


if __name__ == '__main__':
    unittest.main()
